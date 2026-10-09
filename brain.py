"""AI provider boundary for Mafia 1 Pro.

This module intentionally uses a provider-neutral HTTP interface. Configure AI_API_URL,
AI_API_KEY, and AI_MODEL in the environment to connect a compatible chat-completions API.
No API key is embedded in source code.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .security import clean_user_text

DEFAULT_TIMEOUT = 25


def generate_reply(prompt: str, system_prompt: str | None = None) -> str:
    """Call a compatible chat-completions endpoint when configured; otherwise explain setup."""
    prompt = clean_user_text(prompt, limit=8000)
    if not prompt:
        return "اكتب سؤالاً أولاً."

    api_url = os.getenv("AI_API_URL", "").strip()
    api_key = os.getenv("AI_API_KEY", "").strip()
    model = os.getenv("AI_MODEL", "").strip()
    if not api_url or not api_key or not model:
        return (
            "لم يتم ربط مزوّد الذكاء الاصطناعي بعد. أضف AI_API_URL وAI_API_KEY وAI_MODEL "
            "إلى ملف .env باستخدام بيانات مزوّد متوافق، ثم أعد تشغيل البوت."
        )

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt or (
                    "You are the assistant inside Mafia 1 Pro. Give accurate, safe, "
                    "defensive cybersecurity guidance. Only support systems the user "
                    "owns or is authorized to test. Do not provide instructions for "
                    "credential theft, malware deployment, unauthorized access, or evasion."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    request = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT) as response:
            result = json.loads(response.read().decode("utf-8"))
        choices = result.get("choices", [])
        if not choices:
            return "أعاد مزوّد الذكاء الاصطناعي استجابة غير متوقعة."
        content = choices[0].get("message", {}).get("content", "")
        if isinstance(content, list):
            content = "\\n".join(
                part.get("text", "") for part in content if isinstance(part, dict)
            )
        return clean_user_text(str(content), limit=12000) or "لم تصل إجابة نصية من المزوّد."
    except urllib.error.HTTPError as exc:
        return f"تعذّر الاتصال بمزوّد الذكاء الاصطناعي (HTTP {exc.code}). تحقق من إعدادات المزوّد."
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        return f"تعذّر الاتصال بمزوّد الذكاء الاصطناعي: {type(exc).__name__}. تحقق من الاتصال والإعدادات."
