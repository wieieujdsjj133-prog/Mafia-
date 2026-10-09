"""Safe code-generation planning helpers; generated code is never executed here."""
from __future__ import annotations

from .security import clean_user_text


def make_specification(request: str) -> str:
    cleaned = clean_user_text(request, limit=3000)
    if not cleaned:
        return "لم يتم إدخال وصف للمشروع."
    return (
        "مواصفات أولية للمراجعة:\n"
        f"المطلوب: {cleaned}\n"
        "قبل التشغيل: راجع الاعتمادات، اختبر في بيئة معزولة، ولا تشغّل أوامر مجهولة."
    )
