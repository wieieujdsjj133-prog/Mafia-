import re

ALLOWED_TOOLS = {
    "nmap",
    "whois",
    "dnsutils",
    "jq",
}

def normalize_name(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9._-]", "", name)
    return name

def is_allowed(name: str) -> bool:
    return normalize_name(name) in ALLOWED_TOOLS
