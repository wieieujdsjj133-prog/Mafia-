"""Mafia 1 Pro Telegram bot with owner-only project catalog management."""
from __future__ import annotations

import logging
import os
from typing import Optional

import telebot
from telebot import types
from dotenv import load_dotenv

from assistant.assistant import Assistant
from assistant.config import Settings
from assistant.project_manager import (
    add_button, list_buttons, remove_button, create_tool_template, save_uploaded_tool,
)
from virtual_numbers import get_status_message

load_dotenv()
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("mafia1")


def make_bot(settings: Settings) -> telebot.TeleBot:
    return telebot.TeleBot(settings.bot_token, parse_mode=None, threaded=True)


def main() -> None:
    settings = Settings.from_env()
    if not settings.bot_token:
        raise SystemExit("BOT_TOKEN is missing. Copy .env.example to .env and configure it.")

    bot = make_bot(settings)
    assistant = Assistant(owner_id=settings.owner_id)

    def is_owner(user_id: Optional[int]) -> bool:
        return bool(settings.owner_id and user_id == settings.owner_id)

    def main_keyboard(user_id: int) -> types.ReplyKeyboardMarkup:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        keyboard.add(
            types.KeyboardButton("🤖 المساعد"),
            types.KeyboardButton("🛡️ الأمن السيبراني"),
            types.KeyboardButton("🧰 الأدوات"),
            types.KeyboardButton("📱 الأرقام الوهمية"),
            types.KeyboardButton("ℹ️ الحالة"),
        )
        for item in list_buttons():
            keyboard.add(types.KeyboardButton(item["label"]))
        if is_owner(user_id):
            keyboard.add(types.KeyboardButton("⚙️ لوحة المالك"))
        return keyboard

    @bot.message_handler(commands=["start", "help"])
    def start(message: types.Message) -> None:
        user_id = message.from_user.id if message.from_user else 0
        bot.send_message(
            message.chat.id,
            "مرحباً بك في Mafia 1 Pro.\n"
            "يمكن للمساعد شرح مسائل الأمن الدفاعي وتحليل النتائج التي ترسلها.\n"
            "أوامر المالك: /admin /manage /addbutton /removebutton /newtool /tools /status",
            reply_markup=main_keyboard(user_id),
        )

    @bot.message_handler(commands=["id"])
    def show_id(message: types.Message) -> None:
        if message.from_user:
            bot.reply_to(message, f"Telegram user ID: {message.from_user.id}")

    @bot.message_handler(commands=["admin"])
    def admin_command(message: types.Message) -> None:
        user_id = message.from_user.id if message.from_user else 0
        if not is_owner(user_id):
            bot.reply_to(message, "هذا الأمر مخصص للمالك فقط.")
            return
        bot.reply_to(
            message,
            "لوحة إدارة المشروع (للمالك فقط):\n"
            "/manage list — عرض الأزرار\n"
            "/manage addbutton الاسم | عنوان الزر | الوصف | الفئة\n"
            "/manage removebutton الاسم\n"
            "/manage newtool الاسم | الوصف | الفئة\n"
            "/addbutton الاسم | عنوان الزر | الوصف | الفئة\n"
            "/removebutton الاسم\n"
            "/newtool الاسم | الوصف | الفئة\n"
            "أرسل ملف Python كوثيقة لحفظه في tools/custom للمراجعة فقط.\n"
            "الفئات: custom, files, web, cybersecurity, intelligence",
        )

    @bot.message_handler(commands=["manage"])
    def manage_project_command(message: types.Message) -> None:
        """Owner-only, allow-listed project changes. Does not run arbitrary generated code."""
        user_id = message.from_user.id if message.from_user else 0
        if not is_owner(user_id):
            bot.reply_to(message, "إدارة المشروع متاحة للمالك فقط.")
            return
        raw = (message.text or "").partition(" ")[2].strip()
        if not raw:
            bot.reply_to(
                message,
                "أوامر إدارة المشروع:\\n"
                "/manage list\\n"
                "/manage addbutton name | label | description | category\\n"
                "/manage removebutton name\\n"
                "/manage newtool name | description | category",
            )
            return
        action, _, args = raw.partition(" ")
        action = action.strip().lower()
        args = args.strip()
        try:
            if action in {"list", "buttons", "قائمة", "عرض"}:
                items = list_buttons()
                text_out = "\\n".join(
                    f"• {item['name']} — {item['label']} ({item['category']})"
                    for item in items
                ) or "لا توجد أزرار مسجلة."
                bot.reply_to(message, text_out)
            elif action in {"addbutton", "add", "أضف", "اضافة"}:
                parts = [part.strip() for part in args.split("|")]
                if len(parts) < 3:
                    bot.reply_to(message, "الصيغة: /manage addbutton name | label | description | category")
                    return
                result = add_button(parts[0], parts[1], parts[2], parts[3] if len(parts) > 3 else "custom")
                bot.reply_to(message, result, reply_markup=main_keyboard(user_id))
            elif action in {"removebutton", "remove", "delete", "احذف", "حذف"}:
                if not args:
                    bot.reply_to(message, "الصيغة: /manage removebutton name")
                    return
                bot.reply_to(message, remove_button(args), reply_markup=main_keyboard(user_id))
            elif action in {"newtool", "create", "أنشئ", "انشاء"}:
                parts = [part.strip() for part in args.split("|")]
                if len(parts) < 2:
                    bot.reply_to(message, "الصيغة: /manage newtool name | description | category")
                    return
                category = parts[2] if len(parts) > 2 else "custom"
                path = create_tool_template(parts[0], parts[1], category)
                bot.reply_to(
                    message,
                    f"تم إنشاء قالب الأداة: {path.relative_to(path.parents[2])}\\n"
                    "القالب محفوظ للمراجعة، ولم يتم تشغيله تلقائياً.",
                )
            else:
                bot.reply_to(
                    message,
                    "لم أفهم الأمر. استخدم list أو addbutton أو removebutton أو newtool.\\n"
                    "إضافة زر لا تنشئ وظيفة فعلية تلقائياً؛ يجب تنفيذ الأداة ومراجعتها أولاً.",
                )
        except ValueError as exc:
            bot.reply_to(message, str(exc))

    @bot.message_handler(commands=["addbutton"])
    def addbutton_command(message: types.Message) -> None:
        user_id = message.from_user.id if message.from_user else 0
        if not is_owner(user_id):
            bot.reply_to(message, "هذا الأمر مخصص للمالك فقط.")
            return
        raw = (message.text or "").partition(" ")[2]
        parts = [part.strip() for part in raw.split("|")]
        if len(parts) < 3:
            bot.reply_to(message, "الصيغة: /addbutton الاسم | عنوان الزر | الوصف | الفئة")
            return
        try:
            reply = add_button(parts[0], parts[1], parts[2], parts[3] if len(parts) > 3 else "custom")
            bot.reply_to(message, reply, reply_markup=main_keyboard(user_id))
        except ValueError as exc:
            bot.reply_to(message, str(exc))

    @bot.message_handler(commands=["removebutton"])
    def removebutton_command(message: types.Message) -> None:
        user_id = message.from_user.id if message.from_user else 0
        if not is_owner(user_id):
            bot.reply_to(message, "هذا الأمر مخصص للمالك فقط.")
            return
        name = (message.text or "").partition(" ")[2].strip()
        if not name:
            bot.reply_to(message, "الصيغة: /removebutton اسم_الزر")
            return
        try:
            bot.reply_to(message, remove_button(name), reply_markup=main_keyboard(user_id))
        except ValueError as exc:
            bot.reply_to(message, str(exc))

    @bot.message_handler(commands=["newtool"])
    def newtool_command(message: types.Message) -> None:
        user_id = message.from_user.id if message.from_user else 0
        if not is_owner(user_id):
            bot.reply_to(message, "هذا الأمر مخصص للمالك فقط.")
            return
        parts = [part.strip() for part in (message.text or "").partition(" ")[2].split("|")]
        if len(parts) < 2:
            bot.reply_to(message, "الصيغة: /newtool الاسم | وصف الأداة | الفئة")
            return
        category = parts[2] if len(parts) > 2 else "custom"
        try:
            path = create_tool_template(parts[0], parts[1], category)
            bot.reply_to(
                message,
                f"أنشأت قالب الأداة: tools/custom/{path.name}\n"
                "القالب غير مفعّل ولا يُشغّل تلقائياً؛ راجعه واختبره قبل ربطه بزر.",
            )
        except ValueError as exc:
            bot.reply_to(message, str(exc))

    @bot.message_handler(content_types=["document"])
    def upload_python_tool(message: types.Message) -> None:
        user_id = message.from_user.id if message.from_user else 0
        if not is_owner(user_id):
            bot.reply_to(message, "رفع ملفات الأدوات مخصص للمالك فقط.")
            return
        document = message.document
        if not document or not (document.file_name or "").lower().endswith(".py"):
            bot.reply_to(message, "أرسل ملف Python بامتداد .py فقط.")
            return
        if document.file_size and document.file_size > 100_000:
            bot.reply_to(message, "حجم الملف يتجاوز الحد المسموح (100 كيلوبايت).")
            return
        try:
            file_info = bot.get_file(document.file_id)
            content = bot.download_file(file_info.file_path)
            source = content.decode("utf-8")
            ok, result = save_uploaded_tool(document.file_name or "", source)
            bot.reply_to(message, result)
        except UnicodeDecodeError:
            bot.reply_to(message, "تعذر قراءة الملف؛ يجب أن يكون نص Python بترميز UTF-8.")
        except Exception:
            logger.exception("Could not process uploaded tool")
            bot.reply_to(message, "تعذّر فحص الملف أو حفظه. راجع سجل التشغيل.")

    @bot.message_handler(commands=["assistant"])
    def assistant_command(message: types.Message) -> None:
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "استخدم: /assistant اكتب سؤالك هنا")
            return
        user_id = message.from_user.id if message.from_user else 0
        bot.reply_to(message, assistant.respond(parts[1], user_id=user_id))

    @bot.message_handler(commands=["cyber"])
    def cyber_command(message: types.Message) -> None:
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "استخدم: /cyber اشرح نتيجة فحص أو اسأل سؤالاً أمنياً دفاعياً")
            return
        user_id = message.from_user.id if message.from_user else 0
        bot.reply_to(message, assistant.ask_cybersecurity(parts[1], user_id=user_id))

    @bot.message_handler(commands=["finding"])
    def finding_command(message: types.Message) -> None:
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(message, "استخدم: /finding الصق نتيجة الفحص أو السجل بعد إزالة الأسرار")
            return
        user_id = message.from_user.id if message.from_user else 0
        bot.reply_to(message, assistant.analyze_finding(parts[1], user_id=user_id))

    @bot.message_handler(commands=["tools"])
    def tools_command(message: types.Message) -> None:
        items = list_buttons()
        lines = [f"• {item['name']} — {item['label']}: {item['description']}" for item in items]
        bot.reply_to(message, "\n".join(lines) or "لا توجد أدوات مسجلة.")

    @bot.message_handler(commands=["status"])
    def status_command(message: types.Message) -> None:
        user_id = message.from_user.id if message.from_user else 0
        if not is_owner(user_id):
            bot.reply_to(message, "هذا الأمر للمالك فقط.")
            return
        bot.reply_to(
            message,
            "الإعدادات الأساسية:\n"
            f"BOT_TOKEN: {'موجود' if settings.bot_token else 'مفقود'}\n"
            f"OWNER_ID: {'محدد' if settings.owner_id else 'غير محدد'}\n"
            f"الأزرار المخصصة: {sum(1 for item in list_buttons() if item['kind'] == 'custom')}",
        )

    @bot.message_handler(func=lambda m: bool(m.text) and not (m.text or "").startswith("/"))
    def route_message(message: types.Message) -> None:
        text = (message.text or "").strip()
        user_id = message.from_user.id if message.from_user else 0
        chat_id = message.chat.id

        if text == "🤖 المساعد":
            bot.send_message(chat_id, "اكتب /assistant ثم سؤالك. ربط AI يتطلب إعداد AI_API_URL وAI_API_KEY وAI_MODEL.", reply_markup=main_keyboard(user_id))
        elif text == "🛡️ الأمن السيبراني":
            bot.send_message(chat_id, "اسأل المساعد الأمني باستخدام /cyber سؤالك، أو حلّل نتيجة باستخدام /finding النتيجة.", reply_markup=main_keyboard(user_id))
        elif text == "🧰 الأدوات":
            items = list_buttons()
            output = "\n".join(f"• {x['label']}: {x['description']}" for x in items) or "لا توجد أدوات."
            bot.send_message(chat_id, output, reply_markup=main_keyboard(user_id))
        elif text == "📱 الأرقام الوهمية":
            bot.send_message(chat_id, get_status_message())
        elif text == "ℹ️ الحالة":
            bot.send_message(chat_id, "البوت يعمل. استخدم /help للمساعدة.", reply_markup=main_keyboard(user_id))
        elif text == "⚙️ لوحة المالك":
            if not is_owner(user_id):
                bot.send_message(chat_id, "هذا الخيار مخصص للمالك فقط.")
            else:
                bot.send_message(chat_id, "استخدم /admin لعرض أوامر إدارة المشروع.", reply_markup=main_keyboard(user_id))
        else:
            selected = next((x for x in list_buttons() if x["label"] == text), None)
            if selected:
                bot.send_message(
                    chat_id,
                    f"الأداة: {selected['label']}\n{selected['description']}\n"
                    "هذا زر واجهة مسجل. يلزم تنفيذ وظيفة الأداة ومراجعتها قبل أن تنفذ عمليات فعلية.",
                    reply_markup=main_keyboard(user_id),
                )
            else:
                bot.send_message(chat_id, "استخدم /assistant لسؤال المساعد أو /cyber للسؤال الأمني.", reply_markup=main_keyboard(user_id))

    logger.info("Starting Mafia 1 Pro bot")
    try:
        bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=25)
    except KeyboardInterrupt:
        logger.info("Bot stopped by keyboard interrupt")
    except Exception:
        logger.exception("Bot stopped due to an unexpected error")
        raise


if __name__ == "__main__":
    main()
