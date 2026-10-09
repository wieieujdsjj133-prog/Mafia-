"""Safe placeholder for a future legitimate virtual-number provider integration."""
from __future__ import annotations


def get_status_message() -> str:
    return (
        "خدمة الأرقام الافتراضية غير مربوطة بمزوّد حالياً.\n"
        "هذه الواجهة لا تستأجر أرقاماً ولا تستقبل رسائل SMS. "
        "اربط مزوّداً قانونياً عبر API موثّق، واحفظ مفاتيحه في متغيرات البيئة."
    )
