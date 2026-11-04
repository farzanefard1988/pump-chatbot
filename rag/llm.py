"""لایهٔ مدل زبانی (LLM) با چند ارائه‌دهندهٔ قابل‌جایگزین.

providerها:
  - demo   : بدون کلید؛ پاسخ مستند از روی قطعات بازیابی‌شده (اجرای فوری)
  - gemini : Google Gemini (کلید رایگان)
  - ollama : مدل محلی (مثلاً qwen2.5) از طریق Ollama
"""
import textwrap

import config

SYSTEM_PROMPT = textwrap.dedent(
    """
    تو «کارشناس فروش» یک فروشگاه پمپ و الکتروپمپ صنعتی هستی و فارسی صحبت می‌کنی.
    قوانین:
    ۱) فقط و فقط بر اساس «اطلاعات» زیر پاسخ بده. از خودت چیزی اضافه نکن.
    ۲) اگر پاسخ در اطلاعات نبود، صادقانه بگو نمی‌دانی و یک سؤال روشن‌کننده بپرس
       (مثلاً دربارهٔ کاربرد، ارتفاع/فاصلهٔ پمپاژ یا دبی موردنیاز).
    ۳) پاسخ کوتاه، دقیق، فنی و کاربردی باشد.
    ۴) برای انتخاب نهایی پمپ، گرفتن مشاورهٔ فنی و بررسی منحنی عملکرد را توصیه کن.
    """
).strip()


def _build_prompt(query: str, contexts: list) -> str:
    context_text = "\n\n---\n\n".join(c["text"] for c in contexts) or "(اطلاعاتی یافت نشد)"
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"### اطلاعات:\n{context_text}\n\n"
        f"### سؤال کاربر:\n{query}\n\n"
        f"### پاسخ:"
    )


def generate(query: str, contexts: list) -> str:
    provider = config.LLM_PROVIDER
    if provider == "gemini":
        return _gemini(query, contexts)
    if provider == "ollama":
        return _ollama(query, contexts)
    return _demo(query, contexts)


# ----------------------------------------------------------------------------
# حالت دمو: بدون هیچ کلید، پاسخ را از روی مرتبط‌ترین قطعه می‌سازد
# ----------------------------------------------------------------------------
def _demo(query: str, contexts: list) -> str:
    if not contexts:
        return (
            "متأسفم، در پایگاه دانش اطلاعات مرتبطی پیدا نکردم. "
            "می‌تونید سؤالتون رو کمی واضح‌تر یا با جزئیات بیشتر بپرسید؟"
        )
    # برای توضیح، دانش راهنما (نه خودِ محصول) را ترجیح می‌دهیم تا متن با کارت محصول تکراری نشود.
    chosen = next((c for c in contexts if not c.get("product_id")), contexts[0])
    body = chosen["text"]
    # حذف تیترهای markdown
    body = "\n".join(ln for ln in body.split("\n") if not ln.strip().startswith("#")).strip()
    # اگر ناچار قطعهٔ محصول بود، فقط جملهٔ «توضیح» را بردار
    if chosen.get("product_id"):
        for line in body.split("\n"):
            if line.startswith("توضیح:"):
                body = line.replace("توضیح:", "").strip()
                break
    return "بر اساس اطلاعات فروشگاه:\n\n" + body


# ----------------------------------------------------------------------------
# Google Gemini (کلید رایگان)
# ----------------------------------------------------------------------------
def _gemini(query: str, contexts: list) -> str:
    if not config.GOOGLE_API_KEY:
        return "کلید Gemini تنظیم نشده است. متغیر GOOGLE_API_KEY را مقداردهی کنید."
    try:
        import google.generativeai as genai
    except ImportError:
        return "کتابخانهٔ google-generativeai نصب نیست. دستور: pip install google-generativeai"

    genai.configure(api_key=config.GOOGLE_API_KEY)
    model = genai.GenerativeModel(config.GEMINI_MODEL)
    try:
        resp = model.generate_content(_build_prompt(query, contexts))
        return (resp.text or "").strip() or "پاسخی دریافت نشد."
    except Exception as e:  # noqa: BLE001
        return f"خطا در ارتباط با Gemini: {e}"


# ----------------------------------------------------------------------------
# Ollama محلی (مثلاً qwen2.5)
# ----------------------------------------------------------------------------
def _ollama(query: str, contexts: list) -> str:
    import requests

    try:
        resp = requests.post(
            f"{config.OLLAMA_URL}/api/generate",
            json={
                "model": config.OLLAMA_MODEL,
                "prompt": _build_prompt(query, contexts),
                "stream": False,
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip() or "پاسخی دریافت نشد."
    except Exception as e:  # noqa: BLE001
        return f"خطا در ارتباط با Ollama: {e}"
