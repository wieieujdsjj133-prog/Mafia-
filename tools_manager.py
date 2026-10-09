"""Metadata-only tool registry; it does not dynamically execute plugins."""
from __future__ import annotations

from dataclasses import dataclass
from threading import RLock


@dataclass(frozen=True)
class ToolInfo:
    name: str
    description: str
    category: str


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolInfo] = {}
        self._lock = RLock()
        for item in (
            ToolInfo("pdf_metadata", "مكان مخصص لتحليل بيانات PDF محلياً", "files"),
            ToolInfo("dns_lookup", "فحوص DNS أساسية للنطاقات المصرح بها", "cybersecurity"),
            ToolInfo("osint_notes", "تنظيم ملاحظات المصادر المفتوحة", "intelligence"),
        ):
            self.register(item)

    def register(self, tool: ToolInfo) -> None:
        key = tool.name.strip().lower()
        if not key or not key.replace("_", "").isalnum():
            raise ValueError("Tool name must contain letters, numbers, or underscores")
        if not tool.description.strip():
            raise ValueError("Tool description cannot be empty")
        with self._lock:
            self._tools[key] = ToolInfo(key, tool.description.strip(), tool.category.strip())

    def list(self) -> list[dict[str, str]]:
        with self._lock:
            return [
                {"name": item.name, "description": item.description, "category": item.category}
                for item in sorted(self._tools.values(), key=lambda entry: entry.name)
            ]
