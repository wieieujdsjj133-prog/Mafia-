import shutil
import subprocess

from .catalog import TOOLS
from .security import normalize_name, is_allowed


def install_tool(name: str) -> tuple[bool, str]:
    name = normalize_name(name)

    if not is_allowed(name):
        return False, "الأداة غير موجودة في الكتالوج المسموح."

    tool = TOOLS[name]

    if tool["type"] != "apt":
        return False, "نوع التثبيت غير مدعوم."

    if shutil.which("apt-get") is None:
        return False, "apt-get غير متوفر في النظام."

    package = tool["package"]

    try:
        result = subprocess.run(
            ["sudo", "apt-get", "install", "-y", package],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            return False, result.stderr[-2000:]

        return True, f"تم تثبيت {tool['name']} بنجاح."

    except Exception as e:
        return False, str(e)
