from .catalog import TOOLS
from .installer import install_tool
from .security import normalize_name


def find_tool(request: str):
    text = normalize_name(request)

    if text in TOOLS:
        return text

    for key, tool in TOOLS.items():
        if text == normalize_name(tool["name"]):
            return key

    return None


def handle_install_request(request: str) -> str:
    tool = find_tool(request)

    if not tool:
        available = ", ".join(TOOLS.keys())
        return f"الأداة غير موجودة في الكتالوج.\nالأدوات المتاحة: {available}"

    ok, message = install_tool(tool)

    if ok:
        return f"✅ {message}"

    return f"❌ فشل التثبيت:\n{message}"
