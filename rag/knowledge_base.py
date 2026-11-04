"""بارگذاری و قطعه‌بندی (chunk) دانش از فایل‌های Markdown و کاتالوگ محصولات."""
import json
import re
from pathlib import Path

import config


def _split_markdown(md_text: str, source: str) -> list:
    """هر فایل Markdown را بر اساس عنوان‌های ## به قطعات جدا می‌کند."""
    chunks = []
    # جداسازی بر اساس هدینگ‌های سطح دوم
    parts = re.split(r"\n(?=##\s)", md_text)
    for part in parts:
        part = part.strip()
        if not part or part.startswith("# ") and "\n" not in part:
            continue
        # عنوان قطعه را به‌عنوان متادیتا نگه می‌داریم
        title_match = re.match(r"#+\s*(.+)", part)
        title = title_match.group(1).strip() if title_match else source
        if len(part) < 15:
            continue
        chunks.append({"text": part, "source": source, "title": title, "product_id": None})
    return chunks


def load_knowledge() -> list:
    """همهٔ دانش را به شکل فهرستی از قطعات برمی‌گرداند."""
    data_dir: Path = config.DATA_DIR
    chunks = []

    # ۱) فایل‌های Markdown
    for md_file in sorted(data_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        chunks.extend(_split_markdown(text, md_file.name))

    # ۲) کاتالوگ محصولات: هر محصول یک قطعهٔ دانش هم می‌شود
    products = load_products()
    for p in products:
        text = (
            f"محصول: {p['name']}\n"
            f"قیمت: {p['price']:,} تومان\n"
            f"برچسب‌ها: {'، '.join(p.get('tags', []))}\n"
            f"توضیح: {p['description']}"
        )
        chunks.append({
            "text": text,
            "source": "products.json",
            "title": p["name"],
            "product_id": p["id"],
        })

    return chunks


def load_products() -> list:
    """کاتالوگ محصولات را از products.json می‌خواند."""
    path = config.DATA_DIR / "products.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))
