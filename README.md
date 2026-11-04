# 💧 چت‌بات فروش پمپ و الکتروپمپ (فارسی، RAG + مدل رایگان)

یک چت‌بات فارسیِ فروش پمپ صنعتی با دو بخش:

1. **چت‌بات موبایلی (`index.html`)** — صفحهٔ **استاتیک** و مستقل با فلوی مرحله‌به‌مرحله: خوش‌آمد → منوی دسته‌بندی → سؤال‌های پرتکرار → پاسخ + کارت محصول با لینک خرید واقعی → نظرسنجی و گفت‌وگوی جدید. سؤال‌های **تایپ‌آزاد** با مدل رایگان **Google Gemini** و بازیابی از پایگاه دانش (RAG) پاسخ داده می‌شوند.
2. **اپ RAG (`app.py` با Streamlit)** — بازیابی **BM25** روی پایگاه دانشِ مقاله‌محور و پاسخ مستند؛ قابل اتصال به Gemini یا مدل محلی Ollama (کلید سمت سرور).

> پاسخ‌های دانشی از خلاصهٔ مقالات فنی داخلی و خارجی تهیه شده‌اند (منابع در `data/sources.md`). محصولات و لینک‌ها به بازار واقعی ایران (ترب) وصل‌اند.

---

## 🤖 مدل هوش مصنوعی رایگان

این پروژه از **Gemini (سطح رایگان Google AI Studio)** استفاده می‌کند.

- کلید رایگان را از **https://aistudio.google.com/apikey** بگیرید.
- **در `index.html`:** هنگام پرسیدن سؤال تایپ‌آزاد، کلید یک‌بار از شما پرسیده می‌شود و **فقط در مرورگر خودتان (localStorage)** ذخیره می‌شود — در کد یا ریپو قرار نمی‌گیرد. منوی دسته‌بندی و سؤال‌های آماده **بدون کلید** هم کار می‌کنند.
- **در اپ Streamlit:** کلید را به‌صورت متغیر محیطی/Secret بدهید (پایین‌تر).

> ⚠️ چون `index.html` استاتیک است، کلیدِ سمت‌کلاینت در همان مرورگر قابل‌مشاهده است. برای **پروداکشن**، مدل را از سمت سرور (اپ Streamlit یا یک پراکسی) صدا بزنید تا کلید مخفی بماند.

---

## 🚀 دموی آنلاین (GitHub Pages)

`index.html` در ریشهٔ ریپوست؛ با فعال بودن **GitHub Pages** روی شاخهٔ `main`، دمو از این آدرس در دسترس است:

```
https://farzanefard1988.github.io/pump-chatbot/
```

---

## 🖥️ اجرای محلی

### چت‌بات استاتیک
کافی است `index.html` را در مرورگر باز کنید (یا یک سرور ساده):
```bash
python3 -m http.server 8600
# سپس: http://localhost:8600/index.html
```

### اپ RAG با Streamlit
```bash
python3 -m venv .venv
source .venv/bin/activate        # ویندوز: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # برای حالت دمو نیازی به تغییر نیست
streamlit run app.py
```

برای استفاده از Gemini در Streamlit، در `.env`:
```env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=کلید_شما
```

---

## 🧠 افزودن دانش و محصولات خودتان
- **دانش راهنما:** `data/knowledge.md` و `data/faq.md` (هر موضوع زیر یک تیتر `##`). منابع در `data/sources.md`.
- **محصولات:** `data/products.json` (هر محصول: `id`, `name`, `price`, `buy_url`, `tags`, `description`).
- **دسته‌بندی‌ها و سؤال‌های پرتکرار:** `data/categories.json`.
- در `index.html` همین محتوا به‌صورت `PRODUCTS`، `CATS` و `KB` تعبیه شده است.

---

## 📁 ساختار پروژه
```
pump-chatbot/
├── index.html            # چت‌بات موبایلی استاتیک (RAG + Gemini رایگان)
├── app.py                # اپ RAG با Streamlit
├── config.py             # تنظیمات و متغیرهای محیطی
├── .streamlit/config.toml
├── data/                 # knowledge.md, faq.md, sources.md, products.json, categories.json
└── rag/                  # retriever (BM25)، llm (demo/gemini/ollama)، text_utils، knowledge_base
```

---

## ☁️ میزبانی رایگان
- **GitHub Pages** برای `index.html` (همین حالا).
- **Streamlit Community Cloud** یا **Hugging Face Spaces** برای اپ Streamlit؛ کلید `GOOGLE_API_KEY` را به‌صورت **Secret** در تنظیمات میزبان بگذارید، نه داخل کد.
