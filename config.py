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

# انتخاب ارائه‌دهندهٔ مدل زبانی:
#   "demo"   -> بدون هیچ کلید؛ پاسخ مستند از روی دانش (برای اجرای فوری)
#   "gemini" -> Google Gemini (کلید رایگان لازم است)
#   "ollama" -> اجرای محلی با Ollama (مثلاً Qwen 2.5)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "demo").lower()

# کلید رایگان Gemini: از https://aistudio.google.com/apikey بگیرید
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# تنظیمات Ollama محلی
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

# تعداد قطعات بازیابی‌شده برای هر پاسخ
TOP_K = int(os.getenv("TOP_K", "4"))

# درصد مالیات بر ارزش افزوده برای پیش‌فاکتور (نمونه)
VAT_PERCENT = float(os.getenv("VAT_PERCENT", "9"))
