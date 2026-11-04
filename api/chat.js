// تابع سرورلس Vercel: کلید Gemini را سمت سرور نگه می‌دارد.
// index.html به /api/chat درخواست می‌زند و کلید هرگز به مرورگر نمی‌رسد.
// متغیر محیطی لازم در Vercel: GOOGLE_API_KEY  (اختیاری: GEMINI_MODEL)

const SYSTEM_PROMPT =
  'تو «کارشناس فروش» یک فروشگاه پمپ و الکتروپمپ صنعتی هستی و فقط فارسی پاسخ می‌دهی. ' +
  'فقط و فقط بر اساس «اطلاعات» زیر پاسخ بده و از خودت چیزی اضافه نکن. ' +
  'اگر برای توصیهٔ دقیق به جزئیاتی نیاز داری (مثل تعداد طبقات/واحد، عمق چاه، دبی موردنیاز یا نوع سیال) ' +
  'اول یک سؤال کوتاهِ شفاف‌کننده بپرس و پاسخ نهایی نده. پاسخ کوتاه، دقیق و کاربردی باشد.';

// مدل‌های ترجیحیِ کارآمد (flash). مدل سبک (lite) اول است: سریع‌تر و کمتر دچار شلوغی (۵۰۳).
// اگر یکی ۴۰۴/۵۰۳ بدهد سراغ بعدی می‌رویم.
const PREFERRED = [
  'gemini-flash-lite-latest',
  'gemini-3.5-flash',
  'gemini-flash-latest',
  'gemini-3.6-flash',
  'gemini-3.7-flash',
];

// برای سرعت، بدون ListModels؛ مستقیم از مدل‌های ترجیحیِ کارآمد استفاده می‌کنیم.
// اگر یکی ۴۰۴/۵۰۳ بدهد، در حلقهٔ اصلی سراغ بعدی می‌رویم.
function candidateModels() {
  const out = [];
  if (process.env.GEMINI_MODEL) out.push(process.env.GEMINI_MODEL);
  for (const p of PREFERRED) if (!out.includes(p)) out.push(p);
  return out;
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
    const query = (body.query || '').toString().slice(0, 2000);
    const context = (body.context || '').toString().slice(0, 8000);
    if (!query) { res.status(400).json({ error: 'سؤال خالی است.' }); return; }

    const prompt = `${SYSTEM_PROMPT}\n\n### اطلاعات:\n${context || '(اطلاعاتی یافت نشد)'}\n\n### سؤال کاربر:\n${query}\n\n### پاسخ:`;
    const cands = candidateModels();

    let lastStatus = 0;
    for (const model of cands.slice(0, 5)) {
      const r = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${encodeURIComponent(key)}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] }),
        }
      );
      if (r.ok) {
        const data = await r.json();
        const parts = (data && data.candidates && data.candidates[0] && data.candidates[0].content
          && data.candidates[0].content.parts) || [];
        const text = parts.map((p) => p.text || '').join('').trim();
        res.status(200).json({ text: text || 'پاسخی دریافت نشد.' });
        return;
      }
      lastStatus = r.status;
      // ۴۰۴ (مدل منسوخ) یا ۵۰۳ (شلوغی موقت) یا ۵۰۰ → مدل بعدی را امتحان کن
      if (r.status !== 404 && r.status !== 503 && r.status !== 500) break;
    }
    res.status(502).json({ error: `پاسخ از Gemini گرفته نشد (کد ${lastStatus}). کمی بعد دوباره امتحان کنید.` });
  } catch (e) {
    res.status(500).json({ error: 'خطای سرور در ارتباط با Gemini.' });
  }
}
