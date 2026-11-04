"""موتور بازیابی (Retrieval).

به‌صورت پیش‌فرض از BM25 استفاده می‌کند که آفلاین، سریع و بدون نیاز به دانلود
مدل است و برای فارسی (پس از نرمال‌سازی) کیفیت خوبی دارد.

برای ارتقای کیفیت می‌توان از embedding معنایی (Gemini یا sentence-transformers
با مدل bge-m3) استفاده کرد؛ ساختار این کلاس قابل‌جایگزینی است.
"""
from rank_bm25 import BM25Okapi

from rag.text_utils import tokenize


class Retriever:
    def __init__(self, chunks: list):
        self.chunks = chunks
        self._tokenized = [tokenize(c["text"]) for c in chunks]
        self.bm25 = BM25Okapi(self._tokenized)

    def search(self, query: str, k: int = 4) -> list:
        """k قطعهٔ مرتبط‌تر را همراه با امتیاز برمی‌گرداند."""
        tokens = tokenize(query)
        if not tokens:
            return []
        scores = self.bm25.get_scores(tokens)
        ranked = sorted(
            enumerate(scores), key=lambda x: x[1], reverse=True
        )
        results = []
        for idx, score in ranked[:k]:
            if score <= 0:
                continue
            chunk = dict(self.chunks[idx])
            chunk["score"] = float(score)
            results.append(chunk)
        return results
