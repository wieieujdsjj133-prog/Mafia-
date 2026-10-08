from telebot import types
from .catalog import TOOLS
from .registry import load_registry


def tools_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    for key, tool in TOOLS.items():
        keyboard.add(
            types.InlineKeyboardButton(
                tool.get("button", tool["name"]),
                callback_data=f"run_tool:{key}",
            )
        )

    installed = load_registry()

    for name, tool in installed.items():
        callback = f"installed_tool:{name[:40]}"

        keyboard.add(
            types.InlineKeyboardButton(
                f"🧰 {name}",
                callback_data=callback,
            )
        )

    return keyboard
