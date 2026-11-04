"""رابط موبایل فارسی (Streamlit) — چت‌بات فروش پمپ با جریان مرحله‌به‌مرحله.

جریان:
  ۱) خوش‌آمد + بج‌های دسته‌بندی محصولات + امکان تایپ سؤال
  ۲) اگر کاربر دسته‌ای را بزند → سؤال‌های پرتکرار آن دسته نمایش داده می‌شود
  ۳) اگر سؤالی بزند یا تایپ کند → پاسخ مرتبط + پیشنهاد محصول + لینک خرید

اجرا:  streamlit run app.py
"""
import json

import streamlit as st

import config
from rag import llm, sales
from rag.knowledge_base import load_knowledge, load_products
from rag.retriever import Retriever

st.set_page_config(page_title="فروشگاه پمپ", page_icon="💧", layout="centered",
                   initial_sidebar_state="collapsed")

# ===========================  استایل موبایل + فونت IranSans + برندینگ آبی  ===========================
# عرض قاب موبایل بر اساس آیفون (۳۹۳ پیکسل — اندازهٔ آیفون 15/16/17)
PHONE_WIDTH = 393
st.markdown(
    f"""
    <style>
      /* فونت: اگر فایل‌های لایسنس‌دار IranSans را در static/fonts بگذارید، همان استفاده می‌شود؛
         در غیر این صورت وزیرمتن (معادل متن‌باز IranSans) از گوگل‌فونت لود می‌شود. */
      @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700;800&display=swap');
      @font-face {{
        font-family: 'IRANSansX'; font-weight: 400; font-display: swap;
        src: url('app/static/fonts/IRANSansX-Regular.woff2') format('woff2');
      }}
      @font-face {{
        font-family: 'IRANSansX'; font-weight: 700; font-display: swap;
        src: url('app/static/fonts/IRANSansX-Bold.woff2') format('woff2');
      }}

      :root {{
        --brand: #1d4ed8;          /* آبی پررنگ */
        --brand-dark: #1e3a8a;
        --brand-900: #172554;
        --chip-bg: #eff6ff;
        --chip-border: #bfdbfe;
        /* قاب چت‌بات: ارتفاع ثابت ۸۰۰px، عمودی وسط‌چین */
        --frame-h: 800px;
        --input-h: 64px;
        --frame-gap: max(0px, calc((100vh - var(--frame-h)) / 2));
      }}
      * {{ font-family: 'IRANSansX', 'Vazirmatn', Tahoma, sans-serif !important; }}

      /* قاب موبایل: عرض تا سقف ۳۹۳px و ارتفاع ثابت ۸۰۰px، وسط‌چین؛ روی دسکتاپ هم همین قاب می‌ماند */
      html, body, .stApp {{ overflow-x: hidden; }}
      .stApp {{ direction: rtl; background: #e5e7eb; }}
      .stMain {{ background: transparent; }}
      .stMain .block-container {{
        width: 100%; max-width: {PHONE_WIDTH}px !important;
        margin: var(--frame-gap) auto 0 auto !important;
        background: #ffffff;
        height: calc(var(--frame-h) - var(--input-h));   /* بخش گفت‌وگو؛ مابقی برای باکس ورودی */
        max-height: calc(var(--frame-h) - var(--input-h));
        overflow-y: auto;
        padding: 1.2rem 1rem 96px !important;   /* فضای کافی برای نوار اکشن داخل قاب */
        box-shadow: 0 0 44px rgba(0,0,0,0.12);
        border-radius: 24px 24px 0 0;
      }}
      /* نوار اکشن ثابت و کوچک (بازگشت/جستجوی جدید) درست بالای باکس چت، داخل قاب ۸۰۰px */
      .st-key-bottom_actions {{
        position: fixed; bottom: calc(var(--frame-gap) + var(--input-h)); left: 50%; transform: translateX(-50%);
        width: 100%; max-width: {PHONE_WIDTH}px; padding: 4px 1rem 5px;
        background: #ffffff; z-index: 60;
      }}
      /* دو دکمه همیشه افقی کنار هم بمانند (روی موبایل wrap نشوند) */
      .st-key-bottom_actions [data-testid="stHorizontalBlock"] {{
        gap: 6px; flex-wrap: nowrap !important;
      }}
      .st-key-bottom_actions [data-testid="stColumn"] {{
        flex: 1 1 0 !important; width: auto !important; min-width: 0 !important;
      }}
      .st-key-bottom_actions .stButton > button {{
        padding: 3px 6px; font-size: 9.5px; border-radius: 999px; font-weight: 600;
        min-height: 0; white-space: nowrap;
      }}
      /* نوار ورودی ثابت در لبهٔ پایین قاب ۸۰۰px (نه کف صفحه) */
      [data-testid="stBottom"] {{ background: transparent; bottom: var(--frame-gap) !important; }}
      [data-testid="stBottom"] > div {{ background: transparent !important; box-shadow: none; border: none; }}
      [data-testid="stBottomBlockContainer"] {{
        width: 100%; max-width: {PHONE_WIDTH}px !important; margin: 0 auto !important;
        background: #ffffff; border-top: none;
        box-shadow: none;
        border-radius: 0 0 24px 24px;
        padding-top: 0.5rem !important;
        padding-bottom: calc(0.5rem + env(safe-area-inset-bottom)) !important;
      }}

      .stMarkdown, p, h1, h2, h3, label, li {{ text-align: right; }}

      /* حباب‌های گفت‌وگو */
      [data-testid="stChatMessage"] {{ border-radius: 16px; padding: 10px 14px; }}

      /* عنوان منو/بخش‌ها */
      .section-title {{ font-weight: 700; color: var(--brand-dark); margin: 14px 2px 8px; font-size: 14px; }}

      /* دکمه‌ها به شکل آیتم منوی آبی */
      .stButton > button {{
        border-radius: 14px; border: 1.5px solid var(--chip-border);
        background: var(--chip-bg); color: var(--brand-dark); font-weight: 700;
        padding: 12px 16px; width: 100%; transition: all .15s; font-size: 14px;
        box-shadow: none; text-align: right;
      }}
      .stButton > button:hover {{ background: #dbeafe; border-color: var(--brand); color: var(--brand); }}
      .stButton > button[kind="primary"] {{
        background: var(--brand); border-color: var(--brand); color: #fff; border-radius: 999px;
      }}
      .stButton > button[kind="primary"]:hover {{ background: var(--brand-dark); color: #fff; }}

      /* دکمه لینک خرید */
      .stLinkButton > a {{
        border-radius: 999px !important; background: var(--brand) !important;
        color: #fff !important; font-weight: 700 !important; border: none !important;
      }}

      /* کارت محصول */
      .product-card {{
        border: 1px solid #e2e8f0; border-right: 5px solid var(--brand);
        border-radius: 14px; padding: 14px 16px; margin: 8px 0 4px;
        background: #ffffff; box-shadow: 0 2px 10px rgba(15,23,42,0.05);
      }}
      .product-card .pname {{ font-weight: 800; color: var(--brand-900); font-size: 15px; }}
      .product-card .price {{ color: var(--brand); font-weight: 800; font-size: 15px; margin-top: 4px; }}
      .product-card .pdesc {{ color: #475569; font-size: 12.5px; margin-top: 6px; line-height: 1.7; }}

      /* کروسل افقی محصولات (RTL، اسکرول لمسی، پیک کارت بعدی) */
      .carousel {{
        display: flex; direction: rtl; gap: 10px; overflow-x: auto; overflow-y: hidden;
        max-width: 100%; padding: 4px 2px 10px; margin: 2px 0;
        scroll-snap-type: x mandatory; -webkit-overflow-scrolling: touch;
        overscroll-behavior-x: contain;
      }}
      .carousel::-webkit-scrollbar {{ height: 6px; }}
      .carousel::-webkit-scrollbar-thumb {{ background: #cbd5e1; border-radius: 3px; }}
      .ccard {{
        flex: 0 0 auto; width: 240px; scroll-snap-align: start;
        border: 1px solid #e2e8f0; border-top: 4px solid var(--brand);
        border-radius: 14px; padding: 12px 14px; background: #ffffff;
        box-shadow: 0 2px 10px rgba(15,23,42,0.05); display: flex; flex-direction: column;
      }}
      .ccard .pname {{ font-weight: 800; color: var(--brand-900); font-size: 13.5px; line-height: 1.6; }}
      .ccard .price {{ color: var(--brand); font-weight: 800; font-size: 14px; margin-top: 5px; }}
      .ccard .pdesc {{ color: #475569; font-size: 11.5px; margin-top: 7px; line-height: 1.75; }}
      .ccard .buy-mini {{
        margin-top: 12px; display: block; text-align: center; text-decoration: none;
        background: var(--brand); color: #fff !important; border-radius: 999px;
        padding: 8px; font-size: 12.5px; font-weight: 700;
      }}
      .ccard .buy-mini:hover {{ background: var(--brand-dark); }}

      /* عنوان خوش‌آمد (تایتل بالای صفحه) */
      .welcome {{
        color: var(--brand-900); font-weight: 500; font-size: 17px; line-height: 2;
        margin: 4px 2px 2px; text-align: right;
      }}
      .welcome .ask {{ color: var(--brand); font-size: 15px; font-weight: 500; display: block; margin-top: 6px; }}

      header[data-testid="stHeader"] {{ background: transparent; }}
      [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
      [data-testid="collapsedControl"] {{ display: none !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ===========================  بارگذاری موتور و داده  ===========================
@st.cache_resource
def get_engine():
    return Retriever(load_knowledge())


@st.cache_data
def get_categories():
    path = config.DATA_DIR / "categories.json"
    return json.loads(path.read_text(encoding="utf-8"))


retriever = get_engine()
categories = get_categories()
cats_by_id = {c["id"]: c for c in categories}


# ===========================  وضعیت نشست  ===========================
def _init():
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("stage", "home")       # home | category | answered
    st.session_state.setdefault("active_category", None)
    st.session_state.setdefault("last_recommended", [])


_init()


# ===========================  اکشن‌ها (callback)  ===========================
def pick_category(cat_id: str):
    st.session_state.active_category = cat_id
    st.session_state.stage = "category"
    st.session_state.last_recommended = []


def ask(question: str):
    st.session_state.messages.append({"role": "user", "content": question})
    ctx = retriever.search(question, k=config.TOP_K)
    answer = llm.generate(question, ctx)
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.last_recommended = sales.recommend_products(question, ctx)
    st.session_state.stage = "answered"


def go_home():
    st.session_state.stage = "home"
    st.session_state.active_category = None
    st.session_state.last_recommended = []


def reset_all():
    for k in ["messages", "stage", "active_category", "last_recommended"]:
        st.session_state.pop(k, None)
    _init()


# ===========================  عنوان خوش‌آمد (فقط صفحهٔ اول)  ===========================
if st.session_state.stage == "home":
    st.markdown(
        "<div class='welcome'>سلام! 👋 به فروشگاه پمپ و الکتروپمپ خوش اومدی.<br>"
        "چه کمکی می‌تونم بکنم؟"
        "<span class='ask'>در مورد کدام یک از موارد زیر سوال دارید؟</span></div>",
        unsafe_allow_html=True,
    )


# ===========================  تاریخچهٔ گفت‌وگو  ===========================
for msg in st.session_state.messages:
    avatar = "💧" if msg["role"] == "assistant" else "🧑"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])


# ===========================  محصولات پیشنهادی (کروسل افقی قابل‌اسکرول، RTL)  ===========================
if st.session_state.last_recommended:
    st.markdown("<div class='section-title'>🛍️ محصولات پیشنهادی</div>", unsafe_allow_html=True)
    recs = st.session_state.last_recommended[:3]
    cards = "".join(
        f"<div class='ccard'>"
        f"<div class='pname'>{p['name']}</div>"
        f"<div class='price'>از {p['price']:,} تومان</div>"
        f"<div class='pdesc'>{(p['description'][:95] + '…') if len(p['description']) > 98 else p['description']}</div>"
        f"<a class='buy-mini' href='{p['buy_url']}' target='_blank'>🛒 مشاهده در فروشگاه‌ها</a>"
        f"</div>"
        for p in recs
    )
    st.markdown(f"<div class='carousel'>{cards}</div>", unsafe_allow_html=True)


# ===========================  سؤال‌های پرتکرار دسته (مرحلهٔ دسته‌بندی)  ===========================
if st.session_state.stage == "category" and st.session_state.active_category:
    cat = cats_by_id[st.session_state.active_category]
    st.markdown(f"<div class='section-title'>❓ سؤال‌های پرتکرار دستهٔ «{cat['label']}»</div>",
                unsafe_allow_html=True)
    for i, q in enumerate(cat["questions"]):
        st.button(q, key=f"q_{cat['id']}_{i}", on_click=ask, args=(q,), use_container_width=True)


# ===========================  منوی دسته‌بندی (فقط صفحهٔ اول)  ===========================
if st.session_state.stage == "home":
    for cat in categories:
        st.button(f"{cat['icon']}  {cat['label']}", key=f"cat_{cat['id']}",
                  on_click=pick_category, args=(cat["id"],), use_container_width=True)


# ===========================  نوار اکشن ثابت پایین (کنار باکس چت): بازگشت + جستجوی جدید  ===========================
# در صفحهٔ اول نمایش داده نمی‌شود؛ فقط بعد از انتخاب دسته یا پرسیدن سؤال.
if st.session_state.stage in ("category", "answered"):
    with st.container(key="bottom_actions"):
        bcol1, bcol2 = st.columns(2)
        bcol1.button("↩️ بازگشت", key="back_btn", on_click=go_home, use_container_width=True)
        bcol2.button("🔄 جستجوی جدید", key="reset_btn", on_click=reset_all, use_container_width=True)


# ===========================  ورودی تایپ کاربر (ثابت پایین ستون)  ===========================
if prompt := st.chat_input("سؤالتان را بنویسید..."):
    ask(prompt)
    st.rerun()
