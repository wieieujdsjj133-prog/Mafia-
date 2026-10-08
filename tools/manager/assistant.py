from .catalog import TOOLS
from .install import install_apt, install_python_package
from .registry import register_tool
from .search import search_github, search_pypi


def search_tools(query: str):
    github = search_github(query, 5)

    return {
        "github": github,
    }


def install_known_tool(tool_key: str):
    if tool_key not in TOOLS:
        return False, "الأداة غير موجودة في الكتالوج."

    tool = TOOLS[tool_key]

    if tool["type"] == "apt":
        ok, message = install_apt(tool["package"])
    elif tool["type"] == "pip":
        ok, message = install_python_package(tool["package"])
    else:
        return False, "نوع تثبيت غير مدعوم."

    if ok:
        register_tool(
            tool["name"],
            tool["type"],
            tool.get("url", ""),
            tool.get("description", ""),
        )

    return ok, message


def format_search_results(query: str):
    results = search_tools(query)

    github = results["github"]

    if not github:
        return "❌ لم أجد نتائج."

    lines = [
        f"🔎 نتائج البحث عن: {query}",
        "",
    ]

    for index, item in enumerate(github, 1):
        if "error" in item:
            lines.append(f"❌ خطأ: {item['error']}")
            continue

        lines.append(
            f"{index}. {item['name']}\n"
            f"⭐ {item['stars']}\n"
            f"💻 {item['language']}\n"
            f"📝 {item['description'][:200]}\n"
            f"🔗 {item['url']}\n"
        )

    return "\n".join(lines)
