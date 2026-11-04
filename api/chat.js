// تابع سرورلس Vercel: کلید Gemini را سمت سرور نگه می‌دارد.
// index.html به /api/chat درخواست می‌زند و کلید هرگز به مرورگر نمی‌رسد.
// متغیر محیطی لازم در Vercel: GOOGLE_API_KEY  (اختیاری: GEMINI_MODEL)

const SYSTEM_PROMPT =
  'تو «کارشناس فروش» یک فروشگاه پمپ و الکتروپمپ صنعتی هستی و فقط فارسی پاسخ می‌دهی. ' +
  'فقط و فقط بر اساس «اطلاعات» زیر پاسخ بده و از خودت چیزی اضافه نکن. ' +
  'اگر برای توصیهٔ دقیق به جزئیاتی نیاز داری (مثل تعداد طبقات/واحد، عمق چاه، دبی موردنیاز یا نوع سیال) ' +
  'اول یک سؤال کوتاهِ شفاف‌کننده بپرس و پاسخ نهایی نده. پاسخ کوتاه، دقیق و کاربردی باشد.';

// از ListModels مدل‌های در دسترس همان کلید را می‌گیرد و یک مدل مناسب (ترجیحاً flash) برمی‌گرداند
let _cachedModel = null;
async function pickModel(key) {
  if (_cachedModel) return _cachedModel;
  try {
    const r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${encodeURIComponent(key)}`);
    if (!r.ok) return null;
    const data = await r.json();
    const models = (data.models || [])
      .filter((m) => (m.supportedGenerationMethods || []).includes('generateContent'))
      .map((m) => (m.name || '').replace(/^models\//, ''))
      .filter(Boolean);
    const pref = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash'];
    for (const p of pref) {
      const hit = models.find((m) => m === p);
      if (hit) { _cachedModel = hit; return hit; }
    }
    const anyFlash = models.find((m) => m.includes('flash') && !m.includes('vision'));
    _cachedModel = anyFlash || models[0] || null;
    return _cachedModel;
  } catch (e) {
    return null;
  }
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'فقط POST' });
    return;
  }
  const key = process.env.GOOGLE_API_KEY;
  if (!key) {
    res.status(500).json({ error: 'GOOGLE_API_KEY روی سرور تنظیم نشده است.' });
    return;
  }
  try {
    let body = req.body;
    if (typeof body === 'string') { try { body = JSON.parse(body); } catch (e) { body = {}; } }
    body = body || {};

    // حالت تشخیصی (کلید را افشا نمی‌کند): لیست مدل‌ها و نسخهٔ درست API را گزارش می‌دهد
    if (body.debug) {
      const out = {};
      for (const ver of ['v1beta', 'v1']) {
        try {
          const lr = await fetch(`https://generativelanguage.googleapis.com/${ver}/models?key=${encodeURIComponent(key)}`);
          const ld = await lr.json().catch(() => ({}));
          out[ver + '_list_status'] = lr.status;
          out[ver + '_models'] = (ld.models || [])
            .filter((m) => (m.supportedGenerationMethods || []).includes('generateContent'))
            .map((m) => (m.name || '').replace(/^models\//, ''));
          if (ld.error) out[ver + '_err'] = (ld.error.message || '').slice(0, 160);
        } catch (e) { out[ver + '_list_status'] = 'fetch_failed'; }
      }
      const listed = out['v1beta_models'] || [];
      const cands = ['gemini-2.5-flash', 'gemini-flash-latest', 'gemini-flash-lite-latest', 'gemini-2.5-flash-lite', 'gemini-3.5-flash', 'gemini-3.8-flash']
        .filter((m) => listed.includes(m));
      out.gen = {};
      for (const m of cands) {
        try {
          const gr = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${m}:generateContent?key=${encodeURIComponent(key)}`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ contents: [{ parts: [{ text: 'سلام' }] }] }),
          });
          let detail = '';
          if (!gr.ok) { const ej = await gr.json().catch(() => ({})); detail = (ej.error && ej.error.message || '').slice(0, 120); }
          out.gen[m] = gr.status + (detail ? (' | ' + detail) : '');
        } catch (e) { out.gen[m] = 'fetch_failed'; }
      }
      res.status(200).json(out);
      return;
    }

    const query = (body.query || '').toString().slice(0, 2000);
    const context = (body.context || '').toString().slice(0, 8000);
    if (!query) { res.status(400).json({ error: 'سؤال خالی است.' }); return; }

    const prompt = `${SYSTEM_PROMPT}\n\n### اطلاعات:\n${context || '(اطلاعاتی یافت نشد)'}\n\n### سؤال کاربر:\n${query}\n\n### پاسخ:`;

    // انتخاب مدل: اگر GEMINI_MODEL ست شده از آن، وگرنه از لیست مدل‌های همان کلید یک مدل flash بردار
    const model = process.env.GEMINI_MODEL || (await pickModel(key));
    if (!model) {
      res.status(502).json({ error: 'هیچ مدل Gemini در دسترس این کلید پیدا نشد.' });
      return;
    }

    const r = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${encodeURIComponent(key)}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] }),
      }
    );
    if (!r.ok) {
      res.status(502).json({ error: `خطا از Gemini (کد ${r.status}) با مدل ${model}.` });
      return;
    }
    const data = await r.json();
    const parts = (data && data.candidates && data.candidates[0] && data.candidates[0].content
      && data.candidates[0].content.parts) || [];
    const text = parts.map((p) => p.text || '').join('').trim();
    res.status(200).json({ text: text || 'پاسخی دریافت نشد.' });
  } catch (e) {
    res.status(500).json({ error: 'خطای سرور در ارتباط با Gemini.' });
  }
}
