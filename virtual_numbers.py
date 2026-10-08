# virtual_numbers.py
# Mafia 1 — Virtual number management via the owner's Twilio account.
# This module does not automate third-party account verification.

import os
import base64
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from telebot import types

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")

pending_virtual_number = set()


def twilio_ready():
    return bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN)


def twilio_request(method, path, params=None):
    if not twilio_ready():
        raise RuntimeError(
            "لم يتم إعداد TWILIO_ACCOUNT_SID و TWILIO_AUTH_TOKEN في متغيرات البيئة."
        )

    url = "https://api.twilio.com/2010-04-01/Accounts/" + TWILIO_ACCOUNT_SID + "/" + path.lstrip("/")
    data = None
    if params:
        encoded = urlencode(params).encode("utf-8")
        if method.upper() == "GET":
            url += "?" + urlencode(params)
        else:
            data = encoded

    auth = base64.b64encode(
        f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}".encode("utf-8")
    ).decode("ascii")

    req = Request(
        url,
        data=data,
        method=method.upper(),
        headers={
            "Authorization": "Basic " + auth,
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    try:
        with urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            details = json.loads(body)
            msg = details.get("message") or body
        except Exception:
            msg = body
        raise RuntimeError(f"Twilio HTTP {exc.code}: {msg[:500]}")
    except URLError as exc:
        raise RuntimeError(f"تعذر الاتصال بـ Twilio: {exc.reason}")


def twilio_available_numbers(country_code):
    country_code = country_code.strip().upper()
    if not country_code.isalpha() or len(country_code) != 2:
        raise ValueError("استخدم رمز الدولة من حرفين، مثل US أو GB أو DE.")
    return twilio_request(
        "GET",
        f"AvailablePhoneNumbers/{country_code}/Local.json",
        {"SmsEnabled": "true", "PageSize": "5"},
    ).get("available_phone_numbers", [])


def twilio_buy_number(phone_number):
    return twilio_request("POST", "IncomingPhoneNumbers.json", {"PhoneNumber": phone_number})


def twilio_owned_numbers():
    return twilio_request(
        "GET", "IncomingPhoneNumbers.json", {"PageSize": "20"}
    ).get("incoming_phone_numbers", [])


def twilio_release_number(resource_sid):
    return twilio_request("DELETE", f"IncomingPhoneNumbers/{resource_sid}.json")


def virtual_numbers_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton("🌍 اختيار الدولة", callback_data="vn_country"),
        types.InlineKeyboardButton("📋 أرقامي", callback_data="vn_list"),
    )
    kb.row(types.InlineKeyboardButton("⬅️ القائمة الرئيسية", callback_data="main_menu"))
    return kb


def show_virtual_numbers(bot, is_owner, chat_id):
    if not is_owner(chat_id):
        bot.send_message(chat_id, "⛔ أداة الأرقام الافتراضية متاحة للمالك فقط.")
        return
    bot.send_message(
        chat_id,
        "📱 <b>إدارة الأرقام الافتراضية</b>\n\n"
        "يمكنك البحث عن أرقام حقيقية متاحة في حساب Twilio وشراء رقم لحسابك.\n"
        "💳 شراء الرقم قد يترتب عليه رسوم من المزود.\n\n"
        "اختر إجراء:",
        reply_markup=virtual_numbers_menu(),
    )


def show_available_numbers(bot, is_owner, chat_id, country_code):
    if not is_owner(chat_id):
        return
    try:
        numbers = twilio_available_numbers(country_code)
    except Exception as exc:
        bot.send_message(chat_id, f"❌ {exc}")
        return
    if not numbers:
        bot.send_message(chat_id, f"لا توجد أرقام SMS متاحة حالياً للدولة <b>{country_code.upper()}</b>.")
        return
    kb = types.InlineKeyboardMarkup(row_width=1)
    lines = [f"📱 <b>الأرقام المتاحة — {country_code.upper()}</b>\n"]
    for item in numbers[:5]:
        phone = item.get("phone_number", "")
        locality = item.get("locality") or item.get("region") or ""
        label = f"{phone}" + (f" — {locality}" if locality else "")
        kb.add(types.InlineKeyboardButton("شراء " + label, callback_data=f"vn_buy:{phone}"))
        lines.append("• " + label)
    kb.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="virtual_numbers"))
    bot.send_message(chat_id, "\n".join(lines), reply_markup=kb)


def show_owned_numbers(bot, is_owner, chat_id):
    if not is_owner(chat_id):
        return
    try:
        numbers = twilio_owned_numbers()
    except Exception as exc:
        bot.send_message(chat_id, f"❌ {exc}")
        return
    if not numbers:
        bot.send_message(chat_id, "📋 لا توجد أرقام مشتراة في حساب Twilio المرتبط.")
        return
    kb = types.InlineKeyboardMarkup(row_width=1)
    lines = ["📋 <b>أرقامك الحالية</b>\n"]
    for item in numbers[:20]:
        phone = item.get("phone_number", "-")
        sid = item.get("sid", "")
        lines.append(f"• <code>{phone}</code>")
        if sid:
            kb.add(types.InlineKeyboardButton(f"🗑️ تحرير {phone}", callback_data=f"vn_release:{sid}"))
    kb.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="virtual_numbers"))
    bot.send_message(chat_id, "\n".join(lines), reply_markup=kb)


def register_virtual_number_handlers(bot, is_owner, register_user):
    @bot.message_handler(commands=["numbers"])
    def virtual_numbers_command(message):
        register_user(message.from_user)
        if not is_owner(message.from_user.id):
            bot.reply_to(message, "⛔ هذا الأمر متاح للمالك فقط.")
            return
        show_virtual_numbers(bot, is_owner, message.chat.id)

    @bot.message_handler(func=lambda message: message.chat.id in pending_virtual_number)
    def virtual_number_country_message(message):
        if not is_owner(message.from_user.id):
            pending_virtual_number.discard(message.chat.id)
            return
        pending_virtual_number.discard(message.chat.id)
        country = (message.text or "").strip().upper()
        try:
            show_available_numbers(bot, is_owner, message.chat.id, country)
        except Exception as exc:
            bot.send_message(message.chat.id, f"❌ {exc}")


def handle_virtual_callback(bot, is_owner, register_user, call):
    data = call.data or ""
    if not (data == "virtual_numbers" or data in {"vn_country", "vn_list"} or data.startswith("vn_buy:") or data.startswith("vn_release:")):
        return False

    register_user(call.from_user)
    chat_id = call.message.chat.id
    if not is_owner(call.from_user.id):
        bot.answer_callback_query(call.id, "متاح للمالك فقط.", show_alert=True)
        return True

    if data == "virtual_numbers":
        show_virtual_numbers(bot, is_owner, chat_id)
    elif data == "vn_country":
        pending_virtual_number.add(chat_id)
        bot.send_message(chat_id, "🌍 أرسل رمز الدولة من حرفين، مثل:\n<code>US</code> أو <code>GB</code> أو <code>DE</code>")
    elif data == "vn_list":
        show_owned_numbers(bot, is_owner, chat_id)
    elif data.startswith("vn_buy:"):
        phone = data.split(":", 1)[1]
        try:
            purchased = twilio_buy_number(phone)
            purchased_phone = purchased.get("phone_number", phone)
            bot.send_message(chat_id, "✅ <b>تم شراء الرقم</b>\n\n" f"📱 <code>{purchased_phone}</code>\n" f"🆔 <code>{purchased.get('sid', '-')}</code>\n\n" "يمكنك إدارة الرقم من زر «أرقامي»." )
        except Exception as exc:
            bot.send_message(chat_id, f"❌ تعذر شراء الرقم:\n{exc}")
    elif data.startswith("vn_release:"):
        resource_sid = data.split(":", 1)[1]
        try:
            twilio_release_number(resource_sid)
            bot.send_message(chat_id, "✅ تم تحرير الرقم من حساب Twilio.")
        except Exception as exc:
            bot.send_message(chat_id, f"❌ تعذر تحرير الرقم:\n{exc}")

    bot.answer_callback_query(call.id)
    return True
