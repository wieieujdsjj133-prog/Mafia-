"""Assistant facade."""
from __future__ import annotations

from .brain import generate_reply
from .memory import MemoryStore
from .security import clean_user_text
from .tools_manager import ToolRegistry
from tools.cybersecurity import ask_cyber_assistant, analyze_security_finding


class Assistant:
    def __init__(self, owner_id: int | None = None) -> None:
        self.owner_id = owner_id
        self.memory = MemoryStore()
        self.registry = ToolRegistry()

    def respond(self, prompt: str, user_id: int = 0) -> str:
        cleaned = clean_user_text(prompt)
        if not cleaned:
            return "أرسل نصاً واضحاً من فضلك."
        self.memory.add(user_id, "user", cleaned)
        answer = generate_reply(
            cleaned,
            system_prompt=(
                "You are Mafia 1 Pro's senior software engineering and defensive cybersecurity "
                "assistant. Help maintain this project's Python/Telegram architecture, explain "
                "errors, plan tools, review code, analyze authorized security findings, and discuss "
                "public-source OSINT responsibly. Be precise, state assumptions, and do not claim "
                "to have changed files unless a project-management operation actually confirms it. "
                "Do not assist credential theft, malware deployment, unauthorized intrusion, or "
                "stealth/evasion. When the owner wants menu changes, give the exact /manage command. "
                "Adding a menu item is not the same as implementing or executing a tool."
            ),
        )
        self.memory.add(user_id, "assistant", answer)
        return answer

    def ask_cybersecurity(self, prompt: str, user_id: int = 0) -> str:
        cleaned = clean_user_text(prompt)
        if not cleaned:
            return "أرسل سؤالاً أمنياً أولاً."
        self.memory.add(user_id, "user", cleaned)
        answer = ask_cyber_assistant(cleaned)
        self.memory.add(user_id, "assistant", answer)
        return answer

    def analyze_finding(self, finding: str, user_id: int = 0) -> str:
        answer = analyze_security_finding(finding)
        self.memory.add(user_id, "assistant", answer)
        return answer

    def list_tools(self) -> list[dict[str, str]]:
        return self.registry.list()
