"""تنظیمات مرکزی پروژه. مقادیر از متغیرهای محیطی خوانده می‌شوند."""
import os
from pathlib import Path

# تلاش برای بارگذاری فایل .env (اختیاری)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def _get(name: str, default: str = "") -> str:
    """مقدار را اول از متغیر محیطی، سپس از st.secrets (Streamlit Cloud/Spaces) می‌خواند."""
    val = os.getenv(name)
    if val:
        return val
    try:  # روی میزبان، کلید را به‌صورت Secret بگذارید؛ در کد/ریپو نیست
        import streamlit as st  # noqa: WPS433
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:  # noqa: BLE001
        pass
    return default


# کلید رایگان Gemini: از https://aistudio.google.com/apikey بگیرید و روی میزبان به‌صورت Secret بگذارید
GOOGLE_API_KEY = _get("GOOGLE_API_KEY", "")

# انتخاب ارائه‌دهندهٔ مدل زبانی:
#   "demo"   -> بدون هیچ کلید؛ پاسخ مستند از روی دانش (برای اجرای فوری)
#   "gemini" -> Google Gemini (کلید رایگان لازم است)
#   "ollama" -> اجرای محلی با Ollama (مثلاً Qwen 2.5)
# اگر LLM_PROVIDER تنظیم نشده باشد: وجود کلید Gemini -> gemini، در غیر این صورت demo.
LLM_PROVIDER = (_get("LLM_PROVIDER", "") or ("gemini" if GOOGLE_API_KEY else "demo")).lower()

GEMINI_MODEL = _get("GEMINI_MODEL", "gemini-2.0-flash")

# تنظیمات Ollama محلی
OLLAMA_URL = _get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = _get("OLLAMA_MODEL", "qwen2.5:7b")

# تعداد قطعات بازیابی‌شده برای هر پاسخ
TOP_K = int(_get("TOP_K", "4") or "4")

# درصد مالیات بر ارزش افزوده (نمونه)
VAT_PERCENT = float(_get("VAT_PERCENT", "9") or "9")
