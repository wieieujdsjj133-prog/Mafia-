import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
REGISTRY_FILE = BASE_DIR / "installed_tools.json"


def load_registry():
    if not REGISTRY_FILE.exists():
        return {}

    try:
        return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_registry(data):
    REGISTRY_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def register_tool(name, source, url="", description=""):
    data = load_registry()

    data[name] = {
        "name": name,
        "source": source,
        "url": url,
        "description": description,
    }

    save_registry(data)


def remove_tool(name):
    data = load_registry()

    if name in data:
        del data[name]
        save_registry(data)
        return True

    return False
