"""منطق فروش: پیشنهاد محصول، صدور پیش‌فاکتور و تولید لینک پرداخت.

نکته: لینک پرداخت در این MVP «تستی/شبیه‌سازی‌شده» است. برای پرداخت واقعی باید
به درگاه ایرانی (مثل Zarinpal) با کلید مرچنت متصل شوید — جای آن در تابع
create_payment_link مشخص شده است.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime

import config
from rag.knowledge_base import load_products
from rag.text_utils import tokenize


# ----------------------------------------------------------------------------
# پیشنهاد محصول
# ----------------------------------------------------------------------------
def recommend_products(query: str, contexts: list, max_items: int = 3) -> list:
    """بر اساس سؤال کاربر و قطعات بازیابی‌شده، محصولات مرتبط را پیشنهاد می‌دهد."""
    products = load_products()

    # ۱) محصولاتی که مستقیماً در نتایج RAG آمده‌اند، اولویت دارند
    ranked_ids = [c["product_id"] for c in contexts if c.get("product_id")]

    query_tokens = set(tokenize(query))
    scored = []
    for p in products:
        score = 0.0
        # امتیاز از تطابق برچسب‌ها و نام با کلمات سؤال
        hay = set(tokenize(p["name"] + " " + " ".join(p.get("tags", []))))
        score += len(query_tokens & hay) * 2.0
        # امتیاز اضافه اگر محصول در نتایج RAG بوده
        if p["id"] in ranked_ids:
            score += 5.0 - ranked_ids.index(p["id"])  # هرچه بالاتر، امتیاز بیشتر
        if score > 0:
            scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:max_items]]


# ----------------------------------------------------------------------------
# پیش‌فاکتور
# ----------------------------------------------------------------------------
@dataclass
class InvoiceItem:
    product_id: str
    name: str
    unit_price: int
    qty: int = 1

    @property
    def total(self) -> int:
        return self.unit_price * self.qty


@dataclass
class PreInvoice:
    items: list = field(default_factory=list)
    number: str = field(default_factory=lambda: "INV-" + uuid.uuid4().hex[:8].upper())
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

    @property
    def subtotal(self) -> int:
        return sum(i.total for i in self.items)

    @property
    def vat(self) -> int:
        return round(self.subtotal * config.VAT_PERCENT / 100)

    @property
    def grand_total(self) -> int:
        return self.subtotal + self.vat


def build_invoice(cart: dict) -> PreInvoice:
    """cart: نگاشت product_id -> qty. یک پیش‌فاکتور می‌سازد."""
    products = {p["id"]: p for p in load_products()}
    inv = PreInvoice()
    for pid, qty in cart.items():
        if pid in products and qty > 0:
            p = products[pid]
            inv.items.append(InvoiceItem(pid, p["name"], p["price"], qty))
    return inv


# ----------------------------------------------------------------------------
# لینک پرداخت (تستی)
# ----------------------------------------------------------------------------
def create_payment_link(invoice: PreInvoice) -> str:
    """لینک پرداخت تولید می‌کند.

    در این MVP یک لینک سندباکس شبیه‌سازی‌شده برمی‌گرداند. برای اتصال واقعی:
      ۱) درخواست به API درگاه (مثلاً Zarinpal/request) با مبلغ invoice.grand_total
      ۲) دریافت authority/token از پاسخ درگاه
      ۳) ساخت لینک StartPay با آن token و بازگرداندن آن
    """
    token = uuid.uuid4().hex[:24]
    # الگوی سندباکس زرین‌پال (نمونه و غیرواقعی):
    return f"https://sandbox.zarinpal.com/pg/StartPay/{token}"
