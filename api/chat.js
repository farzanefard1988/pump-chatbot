// تابع سرورلس Vercel: کلید Gemini را سمت سرور نگه می‌دارد و پاسخ را «استریم» می‌کند.
// گفت‌وگوی چندمرحله‌ای: تا وقتی اطلاعات کافی نیست فقط سؤال شفاف‌کننده می‌پرسد و محصول پیشنهاد نمی‌دهد؛
// وقتی آماده شد، در خط آخر یک تگ [[RECOMMEND:دسته]] می‌گذارد تا کلاینت محصول نشان دهد.
// متغیر محیطی لازم در Vercel: GOOGLE_API_KEY  (اختیاری: GEMINI_MODEL)

const SYSTEM_PROMPT =
  'تو «کارشناس فروش» یک فروشگاه پمپ و الکتروپمپ صنعتی هستی و فقط فارسی پاسخ می‌دهی. ' +
  'فقط و فقط بر اساس «اطلاعات» زیر پاسخ بده و از خودت چیزی اضافه نکن.\n' +
  'روش کار (مهم): اگر برای پیشنهادِ محصول هنوز اطلاعات کافی نداری، فقط یک سؤالِ کوتاهِ شفاف‌کننده بپرس، ' +
  'هیچ محصولی پیشنهاد نده و هیچ تگی نگذار. هر بار فقط یک سؤال بپرس.\n' +
  'وقتی اطلاعات کافی جمع شد (مثلاً کاربرد، تعداد واحد/طبقه، یا عمق چاه و دبی)، یک پاسخِ نهاییِ کوتاه با ' +
  'توصیهٔ نوع پمپ بده و «دقیقاً در خط آخر» یک تگ در این قالب بگذار:\n[[RECOMMEND:X]]\n' +
  'که X یکی از این مقادیر است: home_pressure, booster, drain, well, industrial, troubleshoot. ' +
  'تا وقتی سؤال می‌پرسی این تگ را نگذار.';

const PREFERRED = [
  'gemini-flash-lite-latest',
  'gemini-3.5-flash',
  'gemini-flash-latest',
  'gemini-3.6-flash',
  'gemini-3.7-flash',
];
function candidateModels() {
  const out = [];
  if (process.env.GEMINI_MODEL) out.push(process.env.GEMINI_MODEL);
  for (const p of PREFERRED) if (!out.includes(p)) out.push(p);
  return out;
}

// یک مدل را استریم می‌کند و هر تکه متن را با onText می‌فرستد
async function streamFrom(model, key, reqBody, onText) {
  const r = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${model}:streamGenerateContent?alt=sse&key=${encodeURIComponent(key)}`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(reqBody) }
  );
  if (!r.ok || !r.body) return { ok: false, status: r.status };
  const reader = r.body.getReader();
  const dec = new TextDecoder();
  let buf = '';
  let any = false;
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let i;
    while ((i = buf.indexOf('\n')) >= 0) {
      const line = buf.slice(0, i).trim();
      buf = buf.slice(i + 1);
      if (!line.startsWith('data:')) continue;
      const p = line.slice(5).trim();
      if (!p || p === '[DONE]') continue;
      try {
        const j = JSON.parse(p);
        const parts = (j && j.candidates && j.candidates[0] && j.candidates[0].content
          && j.candidates[0].content.parts) || [];
        const t = parts.map((x) => x.text || '').join('');
        if (t) { any = true; onText(t); }
      } catch (e) { /* قطعهٔ ناقص SSE */ }
    }
  }
  return { ok: any };
}

export default async function handler(req, res) {
  if (req.method !== 'POST') { res.status(405).json({ error: 'فقط POST' }); return; }
  const key = process.env.GOOGLE_API_KEY;
  if (!key) { res.status(500).json({ error: 'GOOGLE_API_KEY روی سرور تنظیم نشده است.' }); return; }

  let body = req.body;
  if (typeof body === 'string') { try { body = JSON.parse(body); } catch (e) { body = {}; } }
  body = body || {};

  const context = (body.context || '').toString().slice(0, 8000);
  let contents;
  if (Array.isArray(body.history) && body.history.length) {
    contents = body.history
      .filter((m) => m && m.text)
      .map((m) => ({ role: m.role === 'model' ? 'model' : 'user', parts: [{ text: String(m.text).slice(0, 4000) }] }));
  } else {
    const query = (body.query || '').toString().slice(0, 2000);
    if (!query) { res.status(400).json({ error: 'سؤال خالی است.' }); return; }
    contents = [{ role: 'user', parts: [{ text: query }] }];
  }
  if (!contents.length || contents[0].role !== 'user') {
    res.status(400).json({ error: 'ترتیب پیام‌ها نامعتبر است.' });
    return;
  }

  const reqBody = {
    systemInstruction: { parts: [{ text: `${SYSTEM_PROMPT}\n\n### اطلاعات:\n${context || '(اطلاعاتی یافت نشد)'}` }] },
    contents,
  };

  res.setHeader('Content-Type', 'text/plain; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('X-Accel-Buffering', 'no');

  let started = false;
  const write = (t) => { started = true; res.write(t); };
  for (const model of candidateModels().slice(0, 3)) {
    try {
      const result = await streamFrom(model, key, reqBody, write);
      if (result.ok || started) { res.end(); return; }
      // این مدل جواب نداد (۴۰۴/۵۰۳) و چیزی ننوشت → مدل بعدی
    } catch (e) {
      if (started) { res.end(); return; }
    }
  }
  if (!started) { res.statusCode = 502; res.end('[[ERROR]]'); }
}
