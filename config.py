"""Environment-backed configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Settings:
    bot_token: str
    owner_id: Optional[int]

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("BOT_TOKEN", "").strip()
        raw_owner = os.getenv("OWNER_ID", "").strip()
        owner_id: Optional[int] = None
        if raw_owner:
            try:
                owner_id = int(raw_owner)
            except ValueError as exc:
                raise ValueError("OWNER_ID must be a numeric Telegram user ID") from exc
        return cls(bot_token=token, owner_id=owner_id)
