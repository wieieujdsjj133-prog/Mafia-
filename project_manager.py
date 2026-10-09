"""Owner-managed project catalog.

This module changes the bot's JSON catalog and creates reviewed tool templates.
It never deletes project source files and never executes uploaded/generated Python.
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from threading import RLock
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CONFIG_PATH = DATA_DIR / "admin_config.json"
CUSTOM_TOOLS_DIR = ROOT / "tools" / "custom"
_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{1,31}$")
_LABEL_MAX = 40
_DESC_MAX = 240
_LOCK = RLock()

DEFAULT_BUTTONS: list[dict[str, str]] = [
    {"name": "pdf_metadata", "label": "📄 تحليل PDF", "description": "تحليل بيانات ملفات PDF محلياً", "category": "files", "kind": "builtin"},
    {"name": "dns_lookup", "label": "🛡️ مساعد الأمن السيبراني", "description": "شرح النتائج الأمنية والإصلاحات الدفاعية عبر الذكاء الاصطناعي", "category": "cybersecurity", "kind": "builtin"},
    {"name": "osint_notes", "label": "🔎 مساعد الاستخبارات المفتوحة", "description": "بحث وتحليل معلومات المصادر المفتوحة بطريقة مسؤولة", "category": "intelligence", "kind": "builtin"},
]


def _ensure() -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(
            json.dumps({"buttons": DEFAULT_BUTTONS}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {"buttons": DEFAULT_BUTTONS}
    buttons = data.get("buttons")
    if not isinstance(buttons, list):
        buttons = DEFAULT_BUTTONS
    cleaned: list[dict[str, str]] = []
    for item in buttons:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", ""))
        label = str(item.get("label", ""))[:_LABEL_MAX]
        description = str(item.get("description", ""))[:_DESC_MAX]
        category = str(item.get("category", "custom"))[:32]
        kind = str(item.get("kind", "custom"))
        if _NAME_RE.fullmatch(name) and label and description:
            cleaned.append({
                "name": name, "label": label, "description": description,
                "category": category, "kind": kind if kind in {"builtin", "custom"} else "custom",
            })
    data["buttons"] = cleaned
    return data


def list_buttons() -> list[dict[str, str]]:
    with _LOCK:
        return list(_ensure()["buttons"])


def add_button(name: str, label: str, description: str, category: str = "custom") -> str:
    name = (name or "").strip().lower()
    label = (label or "").strip()
    description = (description or "").strip()
    category = (category or "custom").strip().lower()
    if not _NAME_RE.fullmatch(name):
        raise ValueError("الاسم يجب أن يكون بالإنجليزية ويبدأ بحرف، ويحتوي أحرفاً/أرقاماً/شرطة سفلية (2-32 حرفاً).")
    if not label or len(label) > _LABEL_MAX:
        raise ValueError(f"اسم الزر مطلوب وبحد أقصى {_LABEL_MAX} حرفاً.")
    if not description or len(description) > _DESC_MAX:
        raise ValueError(f"الوصف مطلوب وبحد أقصى {_DESC_MAX} حرفاً.")
    with _LOCK:
        data = _ensure()
        if any(item["name"] == name for item in data["buttons"]):
            raise ValueError("يوجد زر بهذا الاسم بالفعل.")
        data["buttons"].append({
            "name": name, "label": label, "description": description,
            "category": category[:32], "kind": "custom",
        })
        CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"تمت إضافة الزر «{label}» إلى القائمة. ملاحظة: الزر يسجل الأداة كعنصر واجهة فقط حتى يتم تنفيذها ومراجعتها."


def remove_button(name: str) -> str:
    name = (name or "").strip().lower()
    with _LOCK:
        data = _ensure()
        target = next((x for x in data["buttons"] if x["name"] == name), None)
        if target is None:
            raise ValueError("لم أجد زرًا بهذا الاسم.")
        # Removing a button only removes its menu/catalog entry; it never deletes source files.
        data["buttons"] = [x for x in data["buttons"] if x["name"] != name]
        CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"تم حذف الزر المخصص «{target['label']}» من القائمة."


def create_tool_template(name: str, description: str, category: str = "custom") -> Path:
    name = (name or "").strip().lower()
    description = (description or "").strip()
    if not _NAME_RE.fullmatch(name):
        raise ValueError("اسم الأداة غير صالح. استخدم أحرفاً إنجليزية صغيرة وأرقاماً وشرطة سفلية.")
    if not description or len(description) > _DESC_MAX:
        raise ValueError("اكتب وصفاً للأداة لا يتجاوز 240 حرفاً.")
    if category not in {"custom", "files", "web", "cybersecurity", "intelligence"}:
        raise ValueError("الفئة غير معروفة.")
    CUSTOM_TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    path = CUSTOM_TOOLS_DIR / f"{name}.py"
    if path.exists():
        raise ValueError("يوجد ملف أداة بهذا الاسم بالفعل.")
    source = (
        '"""Owner-created tool template. Review before enabling."""\n'
        f'NAME = {name!r}\n'
        f'DESCRIPTION = {description!r}\n'
        f'CATEGORY = {category!r}\n\n'
        'def run(input_text: str) -> str:\n'
        '    """Implement a safe, authorized, testable operation here."""\n'
        '    text = (input_text or "").strip()[:4000]\n'
        '    if not text:\n'
        '        return "أدخل بيانات أو سؤالاً أولاً."\n'
        '    return "هذه أداة قالب فقط؛ يلزم تنفيذ الوظيفة ومراجعتها قبل التفعيل."\n'
    )
    ast.parse(source, filename=str(path))
    path.write_text(source, encoding="utf-8")
    return path


_FORBIDDEN_IMPORTS = {
    "subprocess", "socket", "ctypes", "pty", "telnetlib", "ftplib",
    "paramiko", "requests", "httpx", "urllib", "multiprocessing",
}
_FORBIDDEN_CALLS = {
    "eval", "exec", "compile", "__import__", "system", "popen", "remove",
    "unlink", "rmtree", "chmod", "chown",
}


def validate_uploaded_python(source: str) -> tuple[bool, str]:
    """Conservative static checks; this is not a sandbox and cannot prove safety."""
    if len(source.encode("utf-8")) > 100_000:
        return False, "حجم الملف أكبر من 100 كيلوبايت."
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return False, f"خطأ صياغة Python في السطر {exc.lineno}: {exc.msg}"
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name.split(".")[0] for alias in node.names] if isinstance(node, ast.Import) else [(node.module or "").split(".")[0]]
            blocked = sorted(set(names) & _FORBIDDEN_IMPORTS)
            if blocked:
                return False, "استيراد محظور للمراجعة الآمنة: " + ", ".join(blocked)
        if isinstance(node, ast.Call):
            func = node.func
            call_name = func.id if isinstance(func, ast.Name) else (func.attr if isinstance(func, ast.Attribute) else "")
            if call_name in _FORBIDDEN_CALLS:
                return False, f"تم رفض الملف لاحتوائه على استدعاء حساس: {call_name}"
    return True, "اجتاز الفحوصات الساكنة الأولية فقط؛ هذا لا يثبت أن الملف آمن."


def save_uploaded_tool(filename: str, source: str) -> tuple[bool, str]:
    """Store a Python upload for owner review; never imports or executes it."""
    safe_name = Path(filename or "").name
    if not safe_name.endswith(".py") or not _NAME_RE.fullmatch(safe_name[:-3].lower()):
        return False, "اسم الملف يجب أن يكون مثل my_tool.py باستخدام أحرف إنجليزية صغيرة وأرقام وشرطة سفلية."
    ok, message = validate_uploaded_python(source)
    if not ok:
        return False, message
    CUSTOM_TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    destination = CUSTOM_TOOLS_DIR / (safe_name[:-3].lower() + ".py")
    if destination.exists():
        return False, "يوجد ملف بهذا الاسم بالفعل؛ غيّر الاسم أولاً."
    destination.write_text(source, encoding="utf-8")
    return True, (
        f"تم حفظ {destination.name} داخل tools/custom للمراجعة.\n"
        "لم يتم تشغيل الملف أو استيراده تلقائياً. "
        + message
    )
