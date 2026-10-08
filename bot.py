from tools.manager.assistant import handle_install_request
# bot.py
# Telegram Tool Manager - safe modular starter
# Install: pip install pyTelegramBotAPI psutil
# Set: export BOT_TOKEN="YOUR_BOT_TOKEN"
# Optional: export OWNER_ID="123456789"

import os
import sqlite3
import subprocess
import platform
from datetime import datetime

import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0") or 0)

if not BOT_TOKEN:
    raise RuntimeError("ضع BOT_TOKEN في متغير البيئة قبل تشغيل البوت.")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
DB = "bot_factory.db"


# ---------------- Database ----------------

def db():
    return sqlite3.connect(DB)


def register_user(user):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            status TEXT DEFAULT 'free',
            joined_at TEXT
        )
    """)
    cur.execute(
        "INSERT OR IGNORE INTO users(user_id, username, status, joined_at) VALUES(?,?,?,?)",
        (user.id, user.username or "", "free", datetime.now().isoformat())
    )
    cur.execute(
        "UPDATE users SET username=? WHERE user_id=?",
        (user.username or "", user.id)
    )
    conn.commit()
    conn.close()


def is_owner(user_id):
    return OWNER_ID and user_id == OWNER_ID


# ---------------- Menu ----------------

def main_menu(user_id):
    kb = types.InlineKeyboardMarkup(row_width=2)

    buttons = [
        ("🔎 كاشف ID", "id_scan"),
        ("💣 Metasploit", "exploit"),
        ("🌐 Sherlock", "sherlock"),
        ("🔊 تحويل النص لصوت TTS", "tts"),
        ("📡 ماسح الشبكة ARP", "arp"),
        ("🛡️ فحص الروابط", "phish"),
        ("📱 فحص الهاتف", "phone"),
        ("📧 بريد مؤقت", "mail"),
        ("📊 مراقبة Termux", "monitor"),
        ("🤖 مساعد GPT", "gpt"),
        ("🏦 فحص IBAN", "iban"),
        ("📷 فحص الصور ExifTool", "exif"),
        ("📄 محلل PDF", "pdf"),
        ("🔐 فحص المنافذ", "cam_ports"),
        ("🌐 Photon", "photon"),
        ("⚡ Katana", "katana"),
        ("🛡️ فحص WAF", "waf"),
        ("📜 DNS & WHOIS", "dns"),
        ("📦 فحص APK", "apk"),
        ("🔐 أدوات التشفير", "crypto"),
        ("🔑 فحص قوة الباسورد", "pass"),
        ("🔔 مراقب المنافذ", "port_watch"),
        ("📝 صانع الملفات", "file_make"),
        ("🕵️ استخبارات الويب", "dark_web"),
    ]

    for i in range(0, len(buttons), 2):
        row = [types.InlineKeyboardButton(buttons[i][0], callback_data=buttons[i][1])]
        if i + 1 < len(buttons):
            row.append(types.InlineKeyboardButton(buttons[i + 1][0], callback_data=buttons[i + 1][1]))
        kb.row(*row)

    if is_owner(user_id):
        kb.row(
            types.InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="manage_users")
        )

    return kb


# ---------------- Start ----------------

@bot.message_handler(commands=["start"])
def start(message):
    register_user(message.from_user)
    text = (
        "✅ <b>مرحباً بك في مدير الأدوات</b>\n\n"
        "اختر الأداة من القائمة.\n"
        "الأدوات التي تحتاج برنامجاً خارجياً يجب تثبيتها وربطها "
        "بوحدة مستقلة قبل تشغيلها."
    )
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_menu(message.from_user.id)
    )


# ---------------- Callback router ----------------

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    register_user(call.from_user)
    data = call.data
    chat_id = call.message.chat.id

    if data == "monitor":
        monitor(chat_id)

    elif data == "manage_users":
        if not is_owner(call.from_user.id):
            bot.answer_callback_query(call.id, "غير مصرح.", show_alert=True)
            return
        manage_users(chat_id)

    elif data in SAFE_HANDLERS:
        SAFE_HANDLERS[data](chat_id)

    else:
        bot.send_message(
            chat_id,
            "🧩 هذه الواجهة موجودة، لكن تنفيذ الأداة لم يُربط بعد.\n"
            f"<code>{data}</code>\n\n"
            "يمكن ربطها لاحقاً بوحدة مستقلة داخل مجلد tools/."
        )

    bot.answer_callback_query(call.id)


# ---------------- Safe tool handlers ----------------

def monitor(chat_id):
    try:
        uptime = subprocess.check_output(
            ["uptime", "-p"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        uptime = "غير متاح"

    text = (
        "📊 <b>حالة النظام</b>\n\n"
        f"🖥️ النظام: <code>{platform.system()} {platform.release()}</code>\n"
        f"⏱️ التشغيل: <code>{uptime}</code>"
    )

    try:
        import psutil
        text += (
            f"\n🧠 RAM: <code>{psutil.virtual_memory().percent}%</code>"
            f"\n💾 Disk: <code>{psutil.disk_usage('/').percent}%</code>"
        )
    except ImportError:
        text += "\nℹ️ لتفاصيل RAM/Disk: pip install psutil"

    bot.send_message(chat_id, text)


def ask_input(chat_id, title, description):
    bot.send_message(
        chat_id,
        f"🔧 <b>{title}</b>\n\n{description}\n\n"
        "هذه نسخة الواجهة؛ ضع التنفيذ الفعلي في tools/."
    )


def handle_id(chat_id):
    ask_input(chat_id, "كاشف ID", "أرسل معرف Telegram الذي تريد الاستعلام عنه ضمن الصلاحيات المتاحة.")


def handle_tts(chat_id):
    ask_input(chat_id, "TTS", "أرسل النص الذي تريد تحويله إلى صوت.")


def handle_phone(chat_id):
    ask_input(chat_id, "فحص الهاتف", "يمكن إضافة فحوصات محلية آمنة مثل معلومات النظام والمساحة والتطبيقات.")


def handle_mail(chat_id):
    ask_input(chat_id, "البريد المؤقت", "اربط مزود بريد مؤقت عبر API موثوق في وحدة مستقلة.")


def handle_gpt(chat_id):
    ask_input(chat_id, "مساعد GPT", "اربط مزود نموذج الذكاء الاصطناعي عبر API في tools/gpt.py.")


def handle_iban(chat_id):
    ask_input(chat_id, "IBAN", "أرسل رقم IBAN للتحقق من الصيغة فقط، وليس للوصول إلى حسابات مالية.")


def handle_exif(chat_id):
    ask_input(chat_id, "ExifTool", "أرسل صورة لفحص بيانات EXIF الوصفية.")


def handle_pdf(chat_id):
    ask_input(chat_id, "محلل PDF", "أرسل ملف PDF لاستخراج النص والبيانات غير الحساسة.")


def handle_dns(chat_id):
    ask_input(chat_id, "DNS & WHOIS", "أرسل نطاقاً تملكه أو لديك تصريح بفحصه.")


def handle_apk(chat_id):
    ask_input(chat_id, "APK", "أرسل APK لتحليل الأذونات والبيانات الوصفية محلياً.")


def handle_crypto(chat_id):
    ask_input(chat_id, "التشفير", "يمكن إضافة عمليات تشفير وفك تشفير للبيانات التي يملكها المستخدم.")


def handle_password(chat_id):
    ask_input(chat_id, "قوة كلمة المرور", "أرسل كلمة مرور تجريبية فقط؛ لا تحفظ كلمات المرور.")


def handle_file_make(chat_id):
    ask_input(chat_id, "صانع الملفات", "أرسل اسم الملف والمحتوى المطلوب إنشاؤه.")


def handle_web_checks(chat_id):
    ask_input(chat_id, "فحص الويب", "استخدمه فقط على مواقعك أو الأهداف التي لديك تصريح بفحصها.")


SAFE_HANDLERS = {
    "id_scan": handle_id,
    "tts": handle_tts,
    "phone": handle_phone,
    "mail": handle_mail,
    "gpt": handle_gpt,
    "iban": handle_iban,
    "exif": handle_exif,
    "pdf": handle_pdf,
    "dns": handle_dns,
    "apk": handle_apk,
    "crypto": handle_crypto,
    "pass": handle_password,
    "file_make": handle_file_make,
    "phish": handle_web_checks,
    "waf": handle_web_checks,
    "monitor": monitor,
}


# ---------------- Owner panel ----------------

def manage_users(chat_id):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT user_id, username, status FROM users ORDER BY joined_at DESC LIMIT 50")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        bot.send_message(chat_id, "لا يوجد مستخدمون.")
        return

    text = "👥 <b>المستخدمون</b>\n\n"
    for uid, username, status in rows:
        text += f"• <code>{uid}</code> @{username or '-'} — {status}\n"

    bot.send_message(chat_id, text)



# ---------------- Defensive cybersecurity tools ----------------
# These wrappers are intended for systems you own or are explicitly authorized to test.
# Install only the tools you actually need. The bot uses an allowlist and does not expose
# arbitrary shell commands.

import re
import shutil

SECURITY_TOOLS = {
    # Reconnaissance / discovery
    "nmap": {"title": "Nmap", "binary": "nmap", "category": "الاستطلاع", "help": "استكشاف المنافذ والخدمات على هدف مصرح."},
    "masscan": {"title": "Masscan", "binary": "masscan", "category": "الاستطلاع", "help": "اكتشاف المنافذ على نطاق مصرح."},
    "amass": {"title": "Amass", "binary": "amass", "category": "الاستطلاع", "help": "اكتشاف أصول ونطاقات ضمن نطاق مصرح."},
    "subfinder": {"title": "Subfinder", "binary": "subfinder", "category": "الاستطلاع", "help": "اكتشاف النطاقات الفرعية."},
    "assetfinder": {"title": "Assetfinder", "binary": "assetfinder", "category": "الاستطلاع", "help": "اكتشاف الأصول والنطاقات الفرعية."},
    "theharvester": {"title": "theHarvester", "binary": "theHarvester", "category": "الاستطلاع", "help": "جمع معلومات عامة عن نطاق مصرح."},
    "reconng": {"title": "Recon-ng", "binary": "recon-ng", "category": "الاستطلاع", "help": "إطار للاستطلاع الأمني المصرح."},
    "spiderfoot": {"title": "SpiderFoot", "binary": "spiderfoot", "category": "الاستطلاع", "help": "أتمتة جمع المعلومات المفتوحة."},
    "sherlock": {"title": "Sherlock", "binary": "sherlock", "category": "الاستطلاع", "help": "البحث عن أسماء مستخدمين في مصادر عامة."},
    "photon": {"title": "Photon", "binary": "photon", "category": "الاستطلاع", "help": "جمع معلومات من مواقع مصرح بها."},
    "katana": {"title": "Katana", "binary": "katana", "category": "الاستطلاع", "help": "زحف واكتشاف روابط تطبيق ويب مصرح."},
    "httpx": {"title": "httpx", "binary": "httpx", "category": "الاستطلاع", "help": "التحقق من خدمات HTTP/HTTPS."},

    # Web security
    "zap": {"title": "OWASP ZAP", "binary": "zap.sh", "category": "أمن الويب", "help": "اختبار تطبيقات الويب المملوكة أو المصرح بها."},
    "burpsuite": {"title": "Burp Suite", "binary": "burpsuite", "category": "أمن الويب", "help": "اختبار تطبيقات الويب في بيئة مصرح بها."},
    "nuclei": {"title": "Nuclei", "binary": "nuclei", "category": "أمن الويب", "help": "فحص قائم على قوالب معروفة."},
    "nikto": {"title": "Nikto", "binary": "nikto", "category": "أمن الويب", "help": "فحص إعدادات وخدمات ويب على هدف مصرح."},
    "wapiti": {"title": "Wapiti", "binary": "wapiti", "category": "أمن الويب", "help": "فحص تطبيقات ويب مصرح بها."},
    "gobuster": {"title": "Gobuster", "binary": "gobuster", "category": "أمن الويب", "help": "اكتشاف مسارات وموارد في نطاق مصرح."},
    "ffuf": {"title": "ffuf", "binary": "ffuf", "category": "أمن الويب", "help": "اختبار مسارات ومعلمات في بيئة مصرح بها."},
    "whatweb": {"title": "WhatWeb", "binary": "whatweb", "category": "أمن الويب", "help": "التعرف على تقنيات الموقع."},
    "wafw00f": {"title": "WAFW00F", "binary": "wafw00f", "category": "أمن الويب", "help": "التعرف على وجود WAF."},

    # Network analysis / defense
    "wireshark": {"title": "Wireshark", "binary": "wireshark", "category": "الشبكات", "help": "تحليل حركة الشبكة."},
    "tcpdump": {"title": "tcpdump", "binary": "tcpdump", "category": "الشبكات", "help": "التقاط وتحليل الحزم."},
    "zeek": {"title": "Zeek", "binary": "zeek", "category": "الشبكات", "help": "مراقبة وتحليل الشبكات."},
    "suricata": {"title": "Suricata", "binary": "suricata", "category": "الدفاع", "help": "كشف التهديدات ومراقبة الشبكة."},
    "snort": {"title": "Snort", "binary": "snort", "category": "الدفاع", "help": "نظام كشف ومنع التسلل."},

    # Malware / reverse engineering / files
    "ghidra": {"title": "Ghidra", "binary": "ghidra", "category": "تحليل الملفات", "help": "هندسة عكسية وتحليل ملفات."},
    "radare2": {"title": "radare2", "binary": "r2", "category": "تحليل الملفات", "help": "تحليل وهندسة عكسية."},
    "jadx": {"title": "JADX", "binary": "jadx", "category": "Android", "help": "تحليل ملفات APK."},
    "apktool": {"title": "APKTool", "binary": "apktool", "category": "Android", "help": "تحليل موارد APK."},
    "yara": {"title": "YARA", "binary": "yara", "category": "تحليل الملفات", "help": "مطابقة أنماط الملفات والتهديدات."},
    "clamav": {"title": "ClamAV", "binary": "clamscan", "category": "الدفاع", "help": "فحص الملفات بحثاً عن برمجيات خبيثة معروفة."},
    "exiftool": {"title": "ExifTool", "binary": "exiftool", "category": "تحليل الملفات", "help": "قراءة بيانات الملفات الوصفية."},
    "strings": {"title": "strings", "binary": "strings", "category": "تحليل الملفات", "help": "استخراج السلاسل النصية من الملفات."},
    "mobsf": {"title": "MobSF", "binary": "mobsf", "category": "Android", "help": "تحليل أمني لتطبيقات الهاتف."},
    "frida": {"title": "Frida", "binary": "frida", "category": "Android", "help": "تحليل ديناميكي في بيئة اختبار."},

    # Defensive monitoring
    "wazuh": {"title": "Wazuh", "binary": "wazuh-control", "category": "الدفاع", "help": "مراقبة أمنية وإدارة أحداث."},
    "ossec": {"title": "OSSEC", "binary": "ossec-control", "category": "الدفاع", "help": "مراقبة سلامة النظام."},
    "fail2ban": {"title": "Fail2ban", "binary": "fail2ban-client", "category": "الدفاع", "help": "حماية الخدمات من محاولات الدخول المتكررة."},

    # Password auditing / crypto
    "hashcat": {"title": "Hashcat", "binary": "hashcat", "category": "تدقيق كلمات المرور", "help": "تدقيق تجزئات كلمات المرور التي تملكها."},
    "john": {"title": "John the Ripper", "binary": "john", "category": "تدقيق كلمات المرور", "help": "تدقيق تجزئات كلمات المرور المملوكة."},
    "hydra": {"title": "Hydra", "binary": "hydra", "category": "تدقيق كلمات المرور", "help": "اختبار مصادق عليه لخدمات تملكها."},
    "cyberchef": {"title": "CyberChef", "binary": "cyberchef", "category": "التشفير", "help": "تحويل وتحليل بيانات وترميزات."},
    "openssl": {"title": "OpenSSL", "binary": "openssl", "category": "التشفير", "help": "عمليات تشفير وشهادات واتصالات آمنة."},

    # Security assessment frameworks
    "metasploit": {"title": "Metasploit", "binary": "msfconsole", "category": "اختبار أمني", "help": "اختبارات أمنية مصرح بها في مختبر أو نظام تملكه."},
    "searchsploit": {"title": "SearchSploit", "binary": "searchsploit", "category": "اختبار أمني", "help": "البحث المحلي في مراجع الثغرات."},
    "sqlmap": {"title": "SQLMap", "binary": "sqlmap", "category": "اختبار أمني", "help": "اختبار حقن SQL على تطبيق مصرح به."},
    "nessus": {"title": "Nessus", "binary": "nessuscli", "category": "تقييم الثغرات", "help": "تقييم الثغرات في أصول مصرح بها."},
    "openvas": {"title": "OpenVAS / Greenbone", "binary": "gvm-cli", "category": "تقييم الثغرات", "help": "تقييم أمني للبنية التحتية المصرح بها."},
# Additional well-known defensive / assessment tools
"naabu": {"title": "Naabu", "binary": "naabu", "category": "الاستطلاع", "help": "اكتشاف المنافذ في أصول مصرح بها."},
"dnsrecon": {"title": "DNSRecon", "binary": "dnsrecon", "category": "الاستطلاع", "help": "استطلاع DNS على نطاق مصرح."},
"dnsenum": {"title": "DNSenum", "binary": "dnsenum", "category": "الاستطلاع", "help": "تعداد سجلات DNS ضمن نطاق مصرح."},
"fierce": {"title": "Fierce", "binary": "fierce", "category": "الاستطلاع", "help": "استطلاع DNS ونطاقات مصرح بها."},
"gau": {"title": "GAU", "binary": "gau", "category": "الاستطلاع", "help": "جمع عناوين URL العامة لنطاق مصرح."},
"waybackurls": {"title": "Waybackurls", "binary": "waybackurls", "category": "الاستطلاع", "help": "جمع عناوين URL المؤرشفة لنطاق مصرح."},
"hakrawler": {"title": "Hakrawler", "binary": "hakrawler", "category": "الاستطلاع", "help": "زحف ويب في نطاق مصرح."},
"testssl": {"title": "testssl.sh", "binary": "testssl.sh", "category": "أمن الويب", "help": "فحص إعدادات TLS/SSL لخدمة مصرح بها."},
"sslscan": {"title": "SSLScan", "binary": "sslscan", "category": "أمن الويب", "help": "فحص إعدادات SSL/TLS."},
"lynis": {"title": "Lynis", "binary": "lynis", "category": "الدفاع", "help": "تدقيق أمني محلي للنظام."},
"rkhunter": {"title": "Rootkit Hunter", "binary": "rkhunter", "category": "الدفاع", "help": "فحص محلي بحثاً عن مؤشرات rootkit."},
"auditd": {"title": "auditd", "binary": "auditctl", "category": "الدفاع", "help": "تدقيق أحداث النظام محلياً."},
"osqueryi": {"title": "osquery", "binary": "osqueryi", "category": "الدفاع", "help": "استعلامات ومراقبة حالة النظام."},
"trivy": {"title": "Trivy", "binary": "trivy", "category": "تقييم الثغرات", "help": "فحص صور الحاويات والملفات البرمجية."},
"grype": {"title": "Grype", "binary": "grype", "category": "تقييم الثغرات", "help": "فحص البرمجيات بحثاً عن ثغرات معروفة."},
"syft": {"title": "Syft", "binary": "syft", "category": "تحليل الملفات", "help": "إنشاء Software Bill of Materials."},
"semgrep": {"title": "Semgrep", "binary": "semgrep", "category": "تحليل الكود", "help": "تحليل ساكن للكود واكتشاف أنماط أمنية."},
"bandit": {"title": "Bandit", "binary": "bandit", "category": "تحليل الكود", "help": "تحليل أمني لكود Python."},
"gitleaks": {"title": "Gitleaks", "binary": "gitleaks", "category": "تحليل الكود", "help": "اكتشاف الأسرار المكشوفة في المستودعات."},
"trufflehog": {"title": "TruffleHog", "binary": "trufflehog", "category": "تحليل الكود", "help": "اكتشاف أسرار وبيانات اعتماد مكشوفة في مستودعات مصرح بها."},
"checkov": {"title": "Checkov", "binary": "checkov", "category": "تحليل الكود", "help": "فحص إعدادات IaC مثل Terraform وKubernetes."},

    # Additional reconnaissance / web / network tools
    "rustscan": {"title": "RustScan", "binary": "rustscan", "category": "الاستطلاع", "help": "اكتشاف المنافذ في أصول مصرح بها."},
    "uncover": {"title": "Uncover", "binary": "uncover", "category": "الاستطلاع", "help": "البحث في محركات الأصول العامة ضمن نطاق مصرح."},
    "dnsx": {"title": "dnsx", "binary": "dnsx", "category": "الاستطلاع", "help": "التحقق من سجلات DNS لأصول مصرح بها."},
    "puredns": {"title": "PureDNS", "binary": "puredns", "category": "الاستطلاع", "help": "معالجة واختبار أسماء DNS ضمن نطاق مصرح."},
    "dnsx": {"title": "dnsx", "binary": "dnsx", "category": "الاستطلاع", "help": "أدوات DNS سريعة للتحقق من الأصول."},
    "gowitness": {"title": "GoWitness", "binary": "gowitness", "category": "الاستطلاع", "help": "التقاط لقطات لخدمات ويب مصرح بها."},
    "hakcheckurl": {"title": "Hakcheckurl", "binary": "hakcheckurl", "category": "الاستطلاع", "help": "التحقق من عناوين URL."},
    "interactsh-client": {"title": "Interactsh", "binary": "interactsh-client", "category": "اختبار أمني", "help": "اختبار تفاعلات الشبكة في مختبر مصرح."},
    "arjun": {"title": "Arjun", "binary": "arjun", "category": "أمن الويب", "help": "اكتشاف معلمات HTTP في تطبيق مصرح."},
    "dalfox": {"title": "Dalfox", "binary": "dalfox", "category": "أمن الويب", "help": "اختبارات XSS على تطبيق مصرح."},
    "kxss": {"title": "KXSS", "binary": "kxss", "category": "أمن الويب", "help": "تحليل معلمات قد تكون قابلة لاختبار XSS."},
    "uro": {"title": "URO", "binary": "uro", "category": "أمن الويب", "help": "تنظيف وتجميع عناوين URL."},
    "qsreplace": {"title": "qsreplace", "binary": "qsreplace", "category": "أمن الويب", "help": "معالجة معلمات URL في بيئة اختبار."},
    "commix": {"title": "Commix", "binary": "commix", "category": "اختبار أمني", "help": "اختبار حقن أوامر على تطبيق مصرح."},
    "wapiti": {"title": "Wapiti", "binary": "wapiti", "category": "أمن الويب", "help": "فحص تطبيقات ويب مصرح بها."},
    "skipfish": {"title": "Skipfish", "binary": "skipfish", "category": "أمن الويب", "help": "ماسح أمني لتطبيقات الويب في مختبر مصرح."},
    "feroxbuster": {"title": "Feroxbuster", "binary": "feroxbuster", "category": "أمن الويب", "help": "اكتشاف محتوى الويب في نطاق مصرح."},
    "dirsearch": {"title": "Dirsearch", "binary": "dirsearch", "category": "أمن الويب", "help": "اكتشاف مسارات الويب في هدف مصرح."},
    "arjun": {"title": "Arjun", "binary": "arjun", "category": "أمن الويب", "help": "اكتشاف معلمات HTTP."},
    "mitmproxy": {"title": "mitmproxy", "binary": "mitmproxy", "category": "الشبكات", "help": "تحليل HTTP/HTTPS في بيئة اختبار تملكها."},
    "kismet": {"title": "Kismet", "binary": "kismet", "category": "الشبكات", "help": "مراقبة لاسلكية وشبكية دفاعية."},
    "aircrack-ng": {"title": "Aircrack-ng", "binary": "aircrack-ng", "category": "الشبكات", "help": "تدقيق شبكات Wi-Fi المملوكة."},
    "bettercap": {"title": "Bettercap", "binary": "bettercap", "category": "الشبكات", "help": "اختبارات شبكية في مختبر مصرح."},
    "ettercap": {"title": "Ettercap", "binary": "ettercap", "category": "الشبكات", "help": "تحليل شبكي في مختبر مصرح."},
    "arp-scan": {"title": "arp-scan", "binary": "arp-scan", "category": "الشبكات", "help": "اكتشاف أجهزة الشبكة المحلية المملوكة."},
    "netdiscover": {"title": "Netdiscover", "binary": "netdiscover", "category": "الشبكات", "help": "اكتشاف أجهزة الشبكة المحلية."},
    "socat": {"title": "Socat", "binary": "socat", "category": "الشبكات", "help": "أداة اتصالات وشبكات للاختبارات الإدارية."},
    "ncat": {"title": "Ncat", "binary": "ncat", "category": "الشبكات", "help": "اتصالات شبكية للاختبارات والإدارة المصرح بها."},
    "netcat": {"title": "Netcat", "binary": "nc", "category": "الشبكات", "help": "اختبارات اتصال شبكي على أنظمة تملكها."},
    "tshark": {"title": "TShark", "binary": "tshark", "category": "الشبكات", "help": "واجهة سطر أوامر لتحليل الحزم."},
    "arpwatch": {"title": "arpwatch", "binary": "arpwatch", "category": "الدفاع", "help": "مراقبة تغييرات ARP محلياً."},
    "suricata-update": {"title": "Suricata-update", "binary": "suricata-update", "category": "الدفاع", "help": "إدارة قواعد Suricata."},
    "falco": {"title": "Falco", "binary": "falco", "category": "الدفاع", "help": "كشف سلوكيات مشبوهة على الأنظمة والحاويات."},
    "osquery": {"title": "osquery", "binary": "osqueryi", "category": "الدفاع", "help": "استعلام حالة النظام والأجهزة."},
    "velociraptor": {"title": "Velociraptor", "binary": "velociraptor", "category": "الدفاع", "help": "DFIR وجمع أدلة من الأنظمة المملوكة."},
    "sigma": {"title": "Sigma", "binary": "sigma", "category": "الدفاع", "help": "قواعد كشف قابلة للتحويل لأنظمة SIEM."},
    "yara-x": {"title": "YARA-X", "binary": "yr", "category": "تحليل الملفات", "help": "تحليل ومطابقة أنماط الملفات."},
    "capa": {"title": "capa", "binary": "capa", "category": "تحليل الملفات", "help": "تحليل قدرات الملفات التنفيذية."},
    "pefile": {"title": "pefile", "binary": "pefile", "category": "تحليل الملفات", "help": "تحليل ملفات PE عبر بيئة Python."},
    "binwalk": {"title": "Binwalk", "binary": "binwalk", "category": "تحليل الملفات", "help": "تحليل واستخراج محتوى ملفات firmware المملوكة."},
    "foremost": {"title": "Foremost", "binary": "foremost", "category": "تحليل الملفات", "help": "استعادة ملفات من صور أقراص تملكها."},
    "bulk-extractor": {"title": "bulk_extractor", "binary": "bulk_extractor", "category": "تحليل الملفات", "help": "استخراج مؤشرات من صور أقراص مصرح بها."},
    "volatility": {"title": "Volatility", "binary": "vol", "category": "التحقيق الرقمي", "help": "تحليل ذاكرة RAM في التحقيقات المصرح بها."},
    "plaso": {"title": "Plaso", "binary": "log2timeline.py", "category": "التحقيق الرقمي", "help": "بناء خط زمني من أدلة رقمية مملوكة."},
    "autopsy": {"title": "Autopsy", "binary": "autopsy", "category": "التحقيق الرقمي", "help": "تحليل الأدلة الرقمية في بيئة مصرح بها."},
    "sleuthkit": {"title": "The Sleuth Kit", "binary": "fls", "category": "التحقيق الرقمي", "help": "تحليل أنظمة الملفات وصور الأقراص."},
    "impacket": {"title": "Impacket", "binary": "impacket-smbclient", "category": "اختبار أمني", "help": "اختبارات بروتوكولات الشبكات في بيئة مصرح بها."},
    "netexec": {"title": "NetExec", "binary": "nxc", "category": "اختبار أمني", "help": "تقييم خدمات الشبكة في بيئة تملكها."},
    "enum4linux-ng": {"title": "enum4linux-ng", "binary": "enum4linux-ng", "category": "الاستطلاع", "help": "تعداد خدمات SMB في بيئة مصرح بها."},
    "smbclient": {"title": "Samba smbclient", "binary": "smbclient", "category": "الشبكات", "help": "إدارة وفحص مشاركات SMB المملوكة."},
    "ldapsearch": {"title": "ldapsearch", "binary": "ldapsearch", "category": "الشبكات", "help": "استعلام LDAP في بيئة مصرح بها."},
    "bloodhound": {"title": "BloodHound", "binary": "bloodhound", "category": "اختبار أمني", "help": "تحليل علاقات Active Directory في بيئة تملكها."},
    "certipy": {"title": "Certipy", "binary": "certipy", "category": "اختبار أمني", "help": "تدقيق شهادات Active Directory في مختبر مصرح."},
    "responder": {"title": "Responder", "binary": "responder", "category": "اختبار أمني", "help": "اختبارات خدمات المصادقة داخل مختبر مصرح فقط."},
    "prowler": {"title": "Prowler", "binary": "prowler", "category": "السحابة", "help": "تدقيق أمني لحسابات السحابة المملوكة."},
    "scoutsuite": {"title": "ScoutSuite", "binary": "scout", "category": "السحابة", "help": "تقييم إعدادات الخدمات السحابية المملوكة."},
    "checkov": {"title": "Checkov", "binary": "checkov", "category": "السحابة", "help": "فحص IaC مثل Terraform وKubernetes."},
    "kube-bench": {"title": "kube-bench", "binary": "kube-bench", "category": "الحاويات", "help": "فحص إعدادات Kubernetes وفق معايير CIS."},
    "kube-hunter": {"title": "kube-hunter", "binary": "kube-hunter", "category": "الحاويات", "help": "تقييم أمني لعناقيد Kubernetes المملوكة."},
    "trivy-k8s": {"title": "Trivy Kubernetes", "binary": "trivy", "category": "الحاويات", "help": "فحص Kubernetes والصور بحثاً عن مخاطر معروفة."},
    "docker-bench-security": {"title": "Docker Bench Security", "binary": "docker-bench-security.sh", "category": "الحاويات", "help": "تدقيق أمان Docker محلياً."},
    "syft": {"title": "Syft", "binary": "syft", "category": "الحاويات", "help": "إنشاء SBOM للبرمجيات والصور."},
    "grype": {"title": "Grype", "binary": "grype", "category": "الحاويات", "help": "فحص SBOM والصور بحثاً عن CVEs."},
    "dockle": {"title": "Dockle", "binary": "dockle", "category": "الحاويات", "help": "تدقيق أمان صور Docker."},
    "hadolint": {"title": "Hadolint", "binary": "hadolint", "category": "تحليل الكود", "help": "تحليل Dockerfiles."},
    "semgrep": {"title": "Semgrep", "binary": "semgrep", "category": "تحليل الكود", "help": "تحليل ساكن للكود."},
    "sonarqube": {"title": "SonarQube", "binary": "sonar-scanner", "category": "تحليل الكود", "help": "تحليل جودة وأمان الكود."},
    "cppcheck": {"title": "Cppcheck", "binary": "cppcheck", "category": "تحليل الكود", "help": "تحليل ساكن لكود C/C++."},
    "gosec": {"title": "Gosec", "binary": "gosec", "category": "تحليل الكود", "help": "تحليل أمني لكود Go."},
    "eslint": {"title": "ESLint", "binary": "eslint", "category": "تحليل الكود", "help": "تحليل كود JavaScript/TypeScript."},
    "pip-audit": {"title": "pip-audit", "binary": "pip-audit", "category": "تقييم الثغرات", "help": "فحص تبعيات Python بحثاً عن ثغرات."},
    "npm-audit": {"title": "npm audit", "binary": "npm", "category": "تقييم الثغرات", "help": "فحص تبعيات npm."},
    "cargo-audit": {"title": "cargo-audit", "binary": "cargo-audit", "category": "تقييم الثغرات", "help": "فحص تبعيات Rust."},
    "bundle-audit": {"title": "bundler-audit", "binary": "bundle-audit", "category": "تقييم الثغرات", "help": "فحص تبعيات Ruby."},
    "grype": {"title": "Grype", "binary": "grype", "category": "تقييم الثغرات", "help": "فحص الثغرات في الصور والملفات."},
    "opencti": {"title": "OpenCTI", "binary": "opencti", "category": "الاستخبارات", "help": "إدارة معلومات التهديدات."},
    "misp": {"title": "MISP", "binary": "misp", "category": "الاستخبارات", "help": "إدارة ومشاركة مؤشرات التهديد."},
    "thehive": {"title": "TheHive", "binary": "thehive", "category": "الاستجابة للحوادث", "help": "إدارة حالات الاستجابة للحوادث."},
    "cortex": {"title": "Cortex", "binary": "cortex", "category": "الاستجابة للحوادث", "help": "تحليل مؤشرات التهديد في بيئة SOC."},
    "wazuh-agent": {"title": "Wazuh Agent", "binary": "wazuh-agent", "category": "الدفاع", "help": "مراقبة نقاط النهاية."},
    "fail2ban-client": {"title": "Fail2ban Client", "binary": "fail2ban-client", "category": "الدفاع", "help": "إدارة قواعد الحماية المحلية."},
    "clamdscan": {"title": "ClamDScan", "binary": "clamdscan", "category": "الدفاع", "help": "فحص الملفات عبر ClamAV daemon."},
    "freshclam": {"title": "FreshClam", "binary": "freshclam", "category": "الدفاع", "help": "تحديث قواعد ClamAV."},
    "john-the-ripper": {"title": "John the Ripper", "binary": "john", "category": "تدقيق كلمات المرور", "help": "تدقيق تجزئات كلمات المرور التي تملكها."},
    "hashid": {"title": "HashID", "binary": "hashid", "category": "تدقيق كلمات المرور", "help": "التعرف على أنواع التجزئة."},
    "hash-identifier": {"title": "Hash-Identifier", "binary": "hash-identifier", "category": "تدقيق كلمات المرور", "help": "التعرف على أنواع التجزئة."},
    "cewl": {"title": "CeWL", "binary": "cewl", "category": "تدقيق كلمات المرور", "help": "إنشاء قوائم كلمات من محتوى تملكه أو لديك تصريح بتحليله."},
    "openssl": {"title": "OpenSSL", "binary": "openssl", "category": "التشفير", "help": "تشفير وشهادات TLS وأدوات تشفير."},
    "age": {"title": "age", "binary": "age", "category": "التشفير", "help": "تشفير ملفات حديث وبسيط."},
    "gpg": {"title": "GnuPG", "binary": "gpg", "category": "التشفير", "help": "تشفير وتوقيع الملفات والرسائل."},
}


# Expanded catalog: additional widely used security, DFIR, SOC, cloud,
# container, code-security, OSINT and network-analysis tools.
SECURITY_TOOLS.update({
    # OSINT / recon / asset discovery
    "reconftw": {"title":"reconFTW","binary":"reconftw","category":"الاستطلاع","help":"أتمتة الاستطلاع على أصول مصرح بها."},
    "findomain": {"title":"Findomain","binary":"findomain","category":"الاستطلاع","help":"اكتشاف النطاقات الفرعية لأصول مصرح بها."},
    "subjack": {"title":"Subjack","binary":"subjack","category":"الاستطلاع","help":"فحص مؤشرات الاستيلاء على النطاقات الفرعية."},
    "shuffledns": {"title":"ShuffleDNS","binary":"shuffledns","category":"الاستطلاع","help":"معالجة واختبار أسماء DNS المصرح بها."},
    "alterx": {"title":"AlterX","binary":"alterx","category":"الاستطلاع","help":"توليد احتمالات أسماء النطاقات للاختبار المصرح."},
    "mapcidr": {"title":"MapCIDR","binary":"mapcidr","category":"الاستطلاع","help":"معالجة نطاقات IP وCIDR."},
    "tlsx": {"title":"tlsx","binary":"tlsx","category":"الاستطلاع","help":"جمع معلومات شهادات TLS لأصول مصرح بها."},
    "interactsh-client": {"title":"Interactsh Client","binary":"interactsh-client","category":"الاستطلاع","help":"اختبار التفاعلات الشبكية في بيئة مصرح بها."},
    "chaos": {"title":"Chaos","binary":"chaos","category":"الاستطلاع","help":"اكتشاف أصول من بيانات عامة مصرح باستخدامها."},
    "censys": {"title":"Censys CLI","binary":"censys","category":"الاستخبارات","help":"البحث في بيانات الأصول العامة عبر حساب مصرح."},
    "shodan": {"title":"Shodan CLI","binary":"shodan","category":"الاستخبارات","help":"الاستعلام عن بيانات أصول عامة عبر API مصرح."},
    "whois": {"title":"WHOIS","binary":"whois","category":"الاستطلاع","help":"الاستعلام عن بيانات تسجيل النطاقات."},
    "dig": {"title":"dig","binary":"dig","category":"الاستطلاع","help":"استعلام DNS تشخيصي."},
    "host": {"title":"host","binary":"host","category":"الاستطلاع","help":"استعلام DNS تشخيصي."},
    "nslookup": {"title":"nslookup","binary":"nslookup","category":"الاستطلاع","help":"استعلام DNS تشخيصي."},
    "whoislookup": {"title":"whoislookup","binary":"whois","category":"الاستطلاع","help":"استعلام WHOIS."},

    # Web / API security
    "w3af": {"title":"w3af","binary":"w3af_console","category":"أمن الويب","help":"تقييم أمان تطبيقات الويب المصرح بها."},
    "wfuzz": {"title":"Wfuzz","binary":"wfuzz","category":"أمن الويب","help":"اختبار HTTP في بيئة مصرح بها."},
    "feroxbuster": {"title":"Feroxbuster","binary":"feroxbuster","category":"أمن الويب","help":"اكتشاف محتوى الويب في أهداف مصرح بها."},
    "hakrawler": {"title":"Hakrawler","binary":"hakrawler","category":"أمن الويب","help":"زحف واستخراج الروابط من تطبيقات مصرح بها."},
    "dalfox": {"title":"Dalfox","binary":"dalfox","category":"أمن الويب","help":"تحليل مدخلات XSS في تطبيقات مصرح بها."},
    "kxss": {"title":"KXSS","binary":"kxss","category":"أمن الويب","help":"تحليل انعكاس المدخلات في تطبيقات مصرح بها."},
    "qsreplace": {"title":"QSPReplace","binary":"qsreplace","category":"أمن الويب","help":"معالجة معلمات URL للاختبارات المصرح بها."},
    "httpx-toolkit": {"title":"httpx-toolkit","binary":"httpx","category":"أمن الويب","help":"التحقق من خدمات HTTP/HTTPS."},
    "mitmproxy": {"title":"mitmproxy","binary":"mitmproxy","category":"أمن الويب","help":"تحليل HTTP/HTTPS في بيئة اختبار تملكها."},
    "mitmweb": {"title":"mitmweb","binary":"mitmweb","category":"أمن الويب","help":"واجهة ويب لـ mitmproxy في بيئة اختبار."},
    "arachni": {"title":"Arachni","binary":"arachni","category":"أمن الويب","help":"تقييم أمني لتطبيقات الويب المصرح بها."},
    "skipfish": {"title":"Skipfish","binary":"skipfish","category":"أمن الويب","help":"فحص تطبيقات ويب في بيئة مصرح بها."},
    "wapiti-getcookie": {"title":"Wapiti Cookie","binary":"wapiti-getcookie","category":"أمن الويب","help":"مساعدة Wapiti لجلسات الاختبار."},
    "soapui": {"title":"SoapUI","binary":"soapui","category":"أمن الويب","help":"اختبار واجهات SOAP/REST."},
    "postman": {"title":"Postman CLI","binary":"postman","category":"أمن الويب","help":"اختبار APIs المصرح بها."},
    "kiterunner": {"title":"Kiterunner","binary":"kr","category":"أمن الويب","help":"اكتشاف مسارات API في أهداف مصرح بها."},
    "paramspider": {"title":"ParamSpider","binary":"paramspider","category":"أمن الويب","help":"جمع معلمات URL العامة لنطاق مصرح."},
    "uro": {"title":"uro","binary":"uro","category":"أمن الويب","help":"تنظيف ومعالجة قوائم URL."},
    "anew": {"title":"anew","binary":"anew","category":"أمن الويب","help":"إدارة نتائج نصية فريدة في سير العمل."},
    "unfurl": {"title":"unfurl","binary":"unfurl","category":"أمن الويب","help":"تحليل أجزاء عناوين URL."},
    "gobuster-dns": {"title":"Gobuster DNS","binary":"gobuster","category":"أمن الويب","help":"اختبارات DNS مصرح بها عبر Gobuster."},

    # Network / wireless / traffic analysis
    "hping3": {"title":"hping3","binary":"hping3","category":"الشبكات","help":"تشخيص الشبكات في أنظمة تملكها."},
    "mtr": {"title":"mtr","binary":"mtr","category":"الشبكات","help":"تشخيص مسارات الشبكة."},
    "traceroute": {"title":"traceroute","binary":"traceroute","category":"الشبكات","help":"تشخيص مسار الشبكة."},
    "ip": {"title":"iproute2","binary":"ip","category":"الشبكات","help":"إدارة وتشخيص واجهات الشبكة المحلية."},
    "ss": {"title":"ss","binary":"ss","category":"الشبكات","help":"عرض الاتصالات والمنافذ المحلية."},
    "conntrack": {"title":"conntrack","binary":"conntrack","category":"الشبكات","help":"عرض حالة اتصالات النظام."},
    "tcpflow": {"title":"tcpflow","binary":"tcpflow","category":"الشبكات","help":"تحليل تدفقات TCP المسجلة."},
    "netsniff-ng": {"title":"netsniff-ng","binary":"netsniff-ng","category":"الشبكات","help":"تحليل والتقاط الشبكة محلياً."},
    "termshark": {"title":"Termshark","binary":"termshark","category":"الشبكات","help":"واجهة طرفية لـ tshark."},
    "kismet": {"title":"Kismet","binary":"kismet","category":"الشبكات","help":"مراقبة لاسلكية دفاعية للشبكات المملوكة."},
    "iw": {"title":"iw","binary":"iw","category":"الشبكات","help":"إدارة وتشخيص Wi-Fi محلياً."},
    "iwconfig": {"title":"iwconfig","binary":"iwconfig","category":"الشبكات","help":"تشخيص واجهات Wi-Fi."},
    "hostapd": {"title":"hostapd","binary":"hostapd","category":"الشبكات","help":"إدارة نقاط وصول في مختبر مصرح."},

    # Vulnerability / dependency / configuration assessment
    "vuls": {"title":"Vuls","binary":"vuls","category":"تقييم الثغرات","help":"تقييم ثغرات الأنظمة المصرح بها."},
    "lynis-audit": {"title":"Lynis Audit","binary":"lynis","category":"تقييم الثغرات","help":"تدقيق أمني محلي للنظام."},
    "nmap-vuln": {"title":"Nmap NSE","binary":"nmap","category":"تقييم الثغرات","help":"تشخيص خدمات وأصول مصرح بها باستخدام Nmap NSE."},
    "dependency-check": {"title":"OWASP Dependency-Check","binary":"dependency-check","category":"تقييم الثغرات","help":"فحص تبعيات البرمجيات بحثاً عن ثغرات معروفة."},
    "osv-scanner": {"title":"OSV-Scanner","binary":"osv-scanner","category":"تقييم الثغرات","help":"فحص تبعيات ومشاريع برمجية بحثاً عن ثغرات معروفة."},
    "renovate": {"title":"Renovate","binary":"renovate","category":"تقييم الثغرات","help":"إدارة تحديثات التبعيات."},
    "grype-sbom": {"title":"Grype SBOM","binary":"grype","category":"تقييم الثغرات","help":"فحص SBOM بحثاً عن CVEs."},
    "cargo-deny": {"title":"cargo-deny","binary":"cargo-deny","category":"تقييم الثغرات","help":"تدقيق تبعيات Rust والتراخيص."},

    # Code / supply-chain security
    "flawfinder": {"title":"Flawfinder","binary":"flawfinder","category":"تحليل الكود","help":"تحليل ساكن لكود C/C++."},
    "cppcheck-security": {"title":"Cppcheck Security","binary":"cppcheck","category":"تحليل الكود","help":"تحليل ساكن لكود C/C++."},
    "spotbugs": {"title":"SpotBugs","binary":"spotbugs","category":"تحليل الكود","help":"تحليل ساكن لمشاريع Java."},
    "pmd": {"title":"PMD","binary":"pmd","category":"تحليل الكود","help":"تحليل ساكن للكود."},
    "shellcheck": {"title":"ShellCheck","binary":"shellcheck","category":"تحليل الكود","help":"تحليل سكربتات shell."},
    "checkmarx": {"title":"Checkmarx CLI","binary":"cx","category":"تحليل الكود","help":"تكاملات SAST/SCA عند توفر الترخيص."},
    "snyk": {"title":"Snyk CLI","binary":"snyk","category":"تحليل الكود","help":"فحص تبعيات وكود وحاويات عبر حساب مصرح."},
    "secretlint": {"title":"Secretlint","binary":"secretlint","category":"تحليل الكود","help":"كشف أسرار محتملة في الملفات."},
    "detect-secrets": {"title":"detect-secrets","binary":"detect-secrets","category":"تحليل الكود","help":"كشف الأسرار في مستودعات تملكها."},
    "gosec": {"title":"gosec","binary":"gosec","category":"تحليل الكود","help":"تحليل أمني لكود Go."},
    "bearer": {"title":"Bearer","binary":"bearer","category":"تحليل الكود","help":"SAST للعثور على مخاطر أمنية وخصوصية في الكود."},
    "semgrep-ci": {"title":"Semgrep CI","binary":"semgrep","category":"تحليل الكود","help":"تشغيل قواعد SAST على مشروعك."},

    # Containers / Kubernetes / IaC
    "dockle": {"title":"Dockle","binary":"dockle","category":"الحاويات","help":"تدقيق أمان صور Docker."},
    "hadolint": {"title":"Hadolint","binary":"hadolint","category":"الحاويات","help":"تحليل Dockerfiles."},
    "kubeaudit": {"title":"kubeaudit","binary":"kubeaudit","category":"الحاويات","help":"تدقيق إعدادات Kubernetes."},
    "kube-score": {"title":"kube-score","binary":"kube-score","category":"الحاويات","help":"تحليل ملفات Kubernetes."},
    "kube-linter": {"title":"KubeLinter","binary":"kube-linter","category":"الحاويات","help":"فحص manifests الخاصة بـ Kubernetes."},
    "terrascan": {"title":"Terrascan","binary":"terrascan","category":"السحابة","help":"فحص IaC بحثاً عن مخاطر أمنية."},
    "tfsec": {"title":"tfsec","binary":"tfsec","category":"السحابة","help":"تحليل أمان Terraform."},
    "checkov-iac": {"title":"Checkov IaC","binary":"checkov","category":"السحابة","help":"فحص IaC والتهيئات السحابية."},
    "cloudsploit": {"title":"CloudSploit","binary":"cloudsploit","category":"السحابة","help":"تدقيق إعدادات الخدمات السحابية."},
    "prowler-cli": {"title":"Prowler CLI","binary":"prowler","category":"السحابة","help":"تقييم أمان AWS/Azure/GCP المملوكة."},
    "cloudquery": {"title":"CloudQuery","binary":"cloudquery","category":"السحابة","help":"جرد الأصول السحابية وتحليل الامتثال."},
    "steampipe": {"title":"Steampipe","binary":"steampipe","category":"السحابة","help":"استعلام موارد السحابة عبر SQL."},
    "awscli": {"title":"AWS CLI","binary":"aws","category":"السحابة","help":"إدارة وفحص موارد AWS عبر حساب مصرح."},
    "azcli": {"title":"Azure CLI","binary":"az","category":"السحابة","help":"إدارة وفحص موارد Azure عبر حساب مصرح."},
    "gcloud": {"title":"Google Cloud CLI","binary":"gcloud","category":"السحابة","help":"إدارة وفحص موارد GCP عبر حساب مصرح."},

    # DFIR / endpoint / malware analysis
    "sleuthkit-fls": {"title":"Sleuth Kit fls","binary":"fls","category":"التحقيق الرقمي","help":"استعراض أنظمة ملفات الأدلة الرقمية."},
    "istat": {"title":"istat","binary":"istat","category":"التحقيق الرقمي","help":"تحليل metadata لأنظمة الملفات."},
    "mmls": {"title":"mmls","binary":"mmls","category":"التحقيق الرقمي","help":"تحليل تقسيمات صور الأقراص."},
    "blkls": {"title":"blkls","binary":"blkls","category":"التحقيق الرقمي","help":"استخراج كتل من صور أقراص للتحقيق المصرح."},
    "photorec": {"title":"PhotoRec","binary":"photorec","category":"التحقيق الرقمي","help":"استعادة ملفات من وسائط تملكها."},
    "testdisk": {"title":"TestDisk","binary":"testdisk","category":"التحقيق الرقمي","help":"استعادة/تحليل أقسام ووسائط تملكها."},
    "bulk-extractor": {"title":"bulk_extractor","binary":"bulk_extractor","category":"التحقيق الرقمي","help":"استخراج مؤشرات من صور الأدلة الرقمية."},
    "plaso-log2timeline": {"title":"Plaso log2timeline","binary":"log2timeline.py","category":"التحقيق الرقمي","help":"بناء خط زمني للأدلة الرقمية."},
    "timesketch": {"title":"Timesketch","binary":"timesketch","category":"التحقيق الرقمي","help":"تحليل الجداول الزمنية للتحقيقات."},
    "velociraptor": {"title":"Velociraptor","binary":"velociraptor","category":"الاستجابة للحوادث","help":"جمع وتحليل أدلة نقاط النهاية المملوكة."},
    "grr": {"title":"GRR","binary":"grr","category":"الاستجابة للحوادث","help":"استجابة وتحقيق عن بعد على أنظمة مصرح بها."},
    "cylr": {"title":"CyLR","binary":"cylr","category":"الاستجابة للحوادث","help":"جمع artifacts للاستجابة للحوادث."},
    "chainsaw": {"title":"Chainsaw","binary":"chainsaw","category":"الاستجابة للحوادث","help":"تحليل Windows Event Logs."},
    "hayabusa": {"title":"Hayabusa","binary":"hayabusa","category":"الاستجابة للحوادث","help":"تحليل Windows Event Logs وقواعد Sigma."},
    "deepbluecli": {"title":"DeepBlueCLI","binary":"DeepBlue.ps1","category":"الاستجابة للحوادث","help":"تحليل سجلات Windows في بيئة تحقيق مصرح."},
    "sysmon": {"title":"Sysmon","binary":"sysmon","category":"الدفاع","help":"مراقبة نشاط Windows."},
    "loki": {"title":"LOKI","binary":"loki","category":"الدفاع","help":"فحص IOC/YARA لنقاط النهاية المملوكة."},
    "yara-rule-scanner": {"title":"YARA Scanner","binary":"yara","category":"الدفاع","help":"فحص الملفات بقواعد YARA."},
    "strelka": {"title":"Strelka","binary":"strelka","category":"تحليل الملفات","help":"تحليل ملفات على نطاق واسع."},
    "capa": {"title":"capa","binary":"capa","category":"تحليل الملفات","help":"اكتشاف قدرات الملفات التنفيذية."},
    "floss": {"title":"FLOSS","binary":"floss","category":"تحليل الملفات","help":"استخراج السلاسل من الملفات التنفيذية."},
    "detect-it-easy": {"title":"Detect It Easy","binary":"diec","category":"تحليل الملفات","help":"التعرف على packers/compilers في الملفات."},
    "oletools": {"title":"oletools","binary":"olevba","category":"تحليل الملفات","help":"تحليل مستندات Office المصرح بها."},
    "remnux": {"title":"REMnux Tools","binary":"remnux","category":"تحليل الملفات","help":"بيئة أدوات لتحليل البرمجيات الخبيثة."},
    "cape": {"title":"CAPEv2","binary":"cuckoo","category":"تحليل الملفات","help":"تحليل سلوكي للعينات في مختبر معزول."},

    # Threat intelligence / SOC / SIEM
    "sigma-cli": {"title":"Sigma CLI","binary":"sigma","category":"الاستخبارات","help":"تحويل وإدارة قواعد Sigma."},
    "misp-cli": {"title":"MISP CLI","binary":"misp","category":"الاستخبارات","help":"إدارة مؤشرات التهديد عبر خادم مصرح."},
    "cortex-cli": {"title":"Cortex","binary":"cortex","category":"الاستخبارات","help":"تحليل observables عبر منصة SOC."},
    "thehive-cli": {"title":"TheHive","binary":"thehive","category":"الاستجابة للحوادث","help":"إدارة حالات الاستجابة للحوادث."},
    "elastic-agent": {"title":"Elastic Agent","binary":"elastic-agent","category":"الدفاع","help":"جمع ومراقبة أحداث نقاط النهاية."},
    "filebeat": {"title":"Filebeat","binary":"filebeat","category":"الدفاع","help":"جمع السجلات وإرسالها إلى منصات التحليل."},
    "auditbeat": {"title":"Auditbeat","binary":"auditbeat","category":"الدفاع","help":"جمع بيانات تدقيق النظام."},
    "packetbeat": {"title":"Packetbeat","binary":"packetbeat","category":"الدفاع","help":"مراقبة بروتوكولات الشبكة."},
    "graylog": {"title":"Graylog","binary":"graylog","category":"الدفاع","help":"إدارة وتحليل السجلات."},
    "splunk": {"title":"Splunk","binary":"splunk","category":"الدفاع","help":"تحليل السجلات والبيانات الأمنية عبر منصة مصرح بها."},
    "securityonion": {"title":"Security Onion","binary":"so-status","category":"الدفاع","help":"منصة مراقبة وتحليل أمن الشبكات."},
    "arkime": {"title":"Arkime","binary":"capture","category":"الشبكات","help":"التقاط وتحليل حركة الشبكة."},
    "rita": {"title":"RITA","binary":"rita","category":"الدفاع","help":"تحليل مؤشرات التهديد من Zeek."},
    "malcolm": {"title":"Malcolm","binary":"malcolm","category":"الدفاع","help":"تحليل حركة الشبكة والتهديدات."},
    "greynoise": {"title":"GreyNoise CLI","binary":"gnql","category":"الاستخبارات","help":"تحليل ضوضاء المسح من بيانات عامة عبر API مصرح."},
    "virustotal": {"title":"VirusTotal CLI","binary":"vt","category":"الاستخبارات","help":"تحليل ملفات/URLs عبر حساب وAPI مصرح."},

    # Reverse engineering / debugging
    "gdb": {"title":"GDB","binary":"gdb","category":"تحليل الملفات","help":"تصحيح أخطاء البرامج في بيئة تملكها."},
    "lldb": {"title":"LLDB","binary":"lldb","category":"تحليل الملفات","help":"تصحيح أخطاء البرامج."},
    "objdump": {"title":"objdump","binary":"objdump","category":"تحليل الملفات","help":"فحص ملفات ELF والملفات التنفيذية."},
    "readelf": {"title":"readelf","binary":"readelf","category":"تحليل الملفات","help":"تحليل بنية ملفات ELF."},
    "nm": {"title":"nm","binary":"nm","category":"تحليل الملفات","help":"عرض الرموز في الملفات التنفيذية."},
    "patchelf": {"title":"patchelf","binary":"patchelf","category":"تحليل الملفات","help":"فحص/تعديل خصائص ELF في بيئة تملكها."},
    "strace": {"title":"strace","binary":"strace","category":"تحليل الملفات","help":"مراقبة system calls محلياً."},
    "ltrace": {"title":"ltrace","binary":"ltrace","category":"تحليل الملفات","help":"مراقبة استدعاءات المكتبات محلياً."},
    "qemu": {"title":"QEMU","binary":"qemu-system-x86_64","category":"تحليل الملفات","help":"تشغيل بيئات اختبار معزولة."},

    # Mobile
    "adb": {"title":"ADB","binary":"adb","category":"Android","help":"إدارة أجهزة Android المملوكة والمصرح بها."},
    "apk-mitm": {"title":"apk-mitm","binary":"apk-mitm","category":"Android","help":"تهيئة APK للاختبار في بيئة تملكها."},
    "mobsfscan": {"title":"MobSFScan","binary":"mobsfscan","category":"Android","help":"تحليل ساكن لتطبيقات الهاتف."},
    "androguard": {"title":"Androguard","binary":"androguard","category":"Android","help":"تحليل تطبيقات Android."},
    "objection": {"title":"Objection","binary":"objection","category":"Android","help":"تحليل تطبيقات في بيئة اختبار تملكها."},
    "mvt": {"title":"MVT","binary":"mvt-ios","category":"التحقيق الرقمي","help":"تحليل مؤشرات اختراق على أجهزة تملكها."},
    "libimobiledevice": {"title":"libimobiledevice","binary":"idevice_id","category":"التحقيق الرقمي","help":"التعامل مع أجهزة iOS المصرح بها."},

    # Password auditing / crypto / privacy
    "hashid": {"title":"HashID","binary":"hashid","category":"التشفير","help":"التعرف على أنواع التجزئة."},
    "hcxtools": {"title":"hcxtools","binary":"hcxpcapngtool","category":"الشبكات","help":"تحليل captures المملوكة لأغراض التدقيق."},
    "crackmapexec": {"title":"CrackMapExec","binary":"crackmapexec","category":"اختبار أمني","help":"تقييم بيئات Windows المملوكة فقط."},
    "sprayhound": {"title":"SprayHound","binary":"sprayhound","category":"اختبار أمني","help":"تدقيق مصادق عليه لبيئات الهوية."},
    "kerbrute": {"title":"Kerbrute","binary":"kerbrute","category":"اختبار أمني","help":"تدقيق Kerberos في بيئة مصرح بها."},

    # Defensive host hardening
    "chkrootkit": {"title":"chkrootkit","binary":"chkrootkit","category":"الدفاع","help":"فحص محلي بحثاً عن مؤشرات rootkit."},
    "aide": {"title":"AIDE","binary":"aide","category":"الدفاع","help":"مراقبة سلامة الملفات."},
    "rkhunter": {"title":"rkhunter","binary":"rkhunter","category":"الدفاع","help":"فحص مؤشرات rootkit محلياً."},
    "unhide": {"title":"unhide","binary":"unhide","category":"الدفاع","help":"البحث عن عمليات/اتصالات مخفية محلياً."},
    "lynis-command": {"title":"Lynis","binary":"lynis","category":"الدفاع","help":"تدقيق تقوية النظام."},
})


TARGET_RE = re.compile(
    r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?|"
    r"(?:\d{1,3}\.){3}\d{1,3})$"
)


def tool_installed(binary):
    return shutil.which(binary) is not None


def valid_target(target):
    target = target.strip()
    if not TARGET_RE.match(target):
        return False
    if ".." in target or target.startswith(".") or target.endswith("."):
        return False
    return True


def security_menu(user_id):
    kb = types.InlineKeyboardMarkup(row_width=2)
    items = [(k, v["title"]) for k, v in SECURITY_TOOLS.items()]
    for i in range(0, len(items), 2):
        row = [types.InlineKeyboardButton(items[i][1], callback_data=f"sec_{items[i][0]}")]
        if i + 1 < len(items):
            row.append(types.InlineKeyboardButton(items[i + 1][1], callback_data=f"sec_{items[i + 1][0]}"))
        kb.row(*row)
    kb.row(types.InlineKeyboardButton("⬅️ القائمة الرئيسية", callback_data="main_menu"))
    return kb


def category_menu(category):
    kb = types.InlineKeyboardMarkup(row_width=2)
    items = [(k, v["title"]) for k, v in SECURITY_TOOLS.items() if v["category"] == category]
    for i in range(0, len(items), 2):
        row = [types.InlineKeyboardButton(items[i][1], callback_data=f"sec_{items[i][0]}")]
        if i + 1 < len(items):
            row.append(types.InlineKeyboardButton(items[i + 1][1], callback_data=f"sec_{items[i + 1][0]}"))
        kb.row(*row)
    kb.row(types.InlineKeyboardButton("⬅️ رجوع للتصنيفات", callback_data="security_menu"))
    return kb


def all_tools_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    items = list(SECURITY_TOOLS.items())
    for i in range(0, len(items), 2):
        row = [types.InlineKeyboardButton(items[i][1]["title"], callback_data=f"sec_{items[i][0]}")]
        if i + 1 < len(items):
            row.append(types.InlineKeyboardButton(items[i + 1][1]["title"], callback_data=f"sec_{items[i + 1][0]}"))
        kb.row(*row)
    kb.row(types.InlineKeyboardButton("⬅️ رجوع للتصنيفات", callback_data="security_menu"))
    return kb


def security_command(tool_key, target):
    if tool_key == "nmap":
        return ["nmap", "-sV", "--version-light", target]
    if tool_key == "masscan":
        return ["masscan", target, "--ports", "1-1024", "--rate", "100"]
    if tool_key == "subfinder":
        return ["subfinder", "-d", target, "-silent"]
    if tool_key == "assetfinder":
        return ["assetfinder", target]
    if tool_key == "httpx":
        return ["httpx", "-u", target, "-silent", "-status-code", "-title"]
    if tool_key == "nuclei":
        return ["nuclei", "-u", target, "-silent"]
    if tool_key == "whatweb":
        return ["whatweb", target]
    if tool_key == "wafw00f":
        return ["wafw00f", target]
    if tool_key == "nikto":
        return ["nikto", "-h", target]
    if tool_key == "waf":
        return None
    # Tools that require interactive/configured environments are exposed in the
    # catalog but not automatically launched by the bot.
    return None


def run_security_tool(chat_id, tool_key, target):
    info = SECURITY_TOOLS[tool_key]

    if not valid_target(target):
        bot.send_message(chat_id, "❌ الهدف غير صالح. استخدم نطاقاً مثل example.com أو عنوان IP.")
        return

    if not tool_installed(info["binary"]):
        bot.send_message(
            chat_id,
            f"❌ <b>{info['title']}</b> غير مثبتة.\n\n"
            f"ثبّت البرنامج على الجهاز أولاً، ثم أعد المحاولة."
        )
        return

    cmd = security_command(tool_key, target)
    if cmd is None:
        bot.send_message(
            chat_id,
            "🕷️ <b>OWASP ZAP</b>\n\n"
            "تم تجهيز زر الربط، لكن التشغيل النشط يحتاج إعداد ZAP "
            "وتحديد نطاق الاختبار المصرح به قبل تشغيله."
        )
        return

    bot.send_message(
        chat_id,
        f"⏳ جاري تشغيل <b>{info['title']}</b> على <code>{target}</code>..."
    )

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        output = (result.stdout or result.stderr or "").strip()

        if len(output) > 3500:
            output = output[:3500] + "\n… تم اختصار النتيجة."

        if not output:
            output = "لم تُرجع الأداة نتائج."

        bot.send_message(
            chat_id,
            f"📋 <b>{info['title']}</b>\n\n<pre>{output}</pre>"
        )
    except subprocess.TimeoutExpired:
        bot.send_message(chat_id, "⏱️ انتهت مهلة الفحص.")
    except Exception as exc:
        bot.send_message(chat_id, f"❌ حدث خطأ أثناء التشغيل: <code>{exc}</code>")


SECURITY_CALLBACKS = {f"sec_{key}": key for key in SECURITY_TOOLS}

# Store one pending target per chat. This avoids accepting arbitrary shell input.
pending_security = {}


@bot.callback_query_handler(func=lambda call: call.data == "security_menu")
def security_callback(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "🛡️ <b>أدوات الأمن السيبراني</b>\n\n"
        "اختر أداة. استخدمها فقط على أنظمة تملكها أو لديك تصريح باختبارها.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=security_menu(call.from_user.id),
    )


@bot.callback_query_handler(func=lambda call: call.data in CATEGORY_MAP)
def category_callback(call):
    bot.answer_callback_query(call.id)
    category = CATEGORY_MAP[call.data]
    bot.edit_message_text(
        f"🛡️ <b>{category}</b>\n\nاختر الأداة:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=category_menu(category),
    )


@bot.callback_query_handler(func=lambda call: call.data == "cat_all")
def all_tools_callback(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "🛡️ <b>كل أدوات الأمن السيبراني</b>\n\nاختر الأداة:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=all_tools_menu(),
    )


@bot.callback_query_handler(func=lambda call: call.data in SECURITY_CALLBACKS)
def security_tool_callback(call):
    bot.answer_callback_query(call.id)
    tool_key = SECURITY_CALLBACKS[call.data]
    pending_security[call.message.chat.id] = tool_key
    info = SECURITY_TOOLS[tool_key]

    bot.send_message(
        call.message.chat.id,
        f"🔧 <b>{info['title']}</b>\n\n"
        f"{info['help']}\n\n"
        "أرسل اسم النطاق أو عنوان IP المصرح لك بفحصه."
    )


@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def main_menu_callback(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "🏠 <b>القائمة الرئيسية</b>",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=main_menu(call.from_user.id),
    )


@bot.message_handler(func=lambda message: message.chat.id in pending_security)
def security_target_message(message):
    tool_key = pending_security.pop(message.chat.id)
    run_security_tool(message.chat.id, tool_key, message.text)


# Add the security-tools button to the existing main menu.
_original_main_menu = main_menu


def main_menu(user_id):
    kb = _original_main_menu(user_id)
    kb.row(types.InlineKeyboardButton("🛡️ أشهر أدوات الأمن السيبراني", callback_data="security_menu"))
    return kb




# ---------------- Automatic tool activation/status ----------------

def security_tools_status():
    """Return installed/uninstalled state for every catalogued tool."""
    result = []
    for key, info in SECURITY_TOOLS.items():
        result.append((key, info["title"], info["binary"], tool_installed(info["binary"])))
    return result


@bot.callback_query_handler(func=lambda call: call.data == "tools_status")
def tools_status_callback(call):
    bot.answer_callback_query(call.id)
    rows = security_tools_status()

    installed = [x for x in rows if x[3]]
    missing = [x for x in rows if not x[3]]

    text = (
        "⚙️ <b>حالة الأدوات</b>\n\n"
        f"✅ مثبتة: <b>{len(installed)}</b>\n"
        f"❌ غير مثبتة: <b>{len(missing)}</b>\n\n"
    )

    if installed:
        text += "<b>✅ مثبتة:</b>\n"
        text += "\n".join(f"• {x[1]}" for x in installed[:40])

    if missing:
        text += "\n\n<b>❌ تحتاج تثبيت/إعداد:</b>\n"
        text += "\n".join(f"• {x[1]}" for x in missing[:40])

    bot.send_message(call.message.chat.id, text)


def install_command_for(tool_key):
    """Return a package-manager command suggestion, never execute it automatically."""
    apt = {
        "nmap": "nmap",
        "masscan": "masscan",
        "nikto": "nikto",
        "gobuster": "gobuster",
        "ffuf": "ffuf",
        "wireshark": "wireshark",
        "tcpdump": "tcpdump",
        "snort": "snort",
        "yara": "yara",
        "clamav": "clamav",
        "exiftool": "libimage-exiftool-perl",
        "john": "john",
        "hydra": "hydra",
        "openssl": "openssl",
        "sqlmap": "sqlmap",
        "fail2ban": "fail2ban",
    }
    if tool_key in apt:
        return f"sudo apt update && sudo apt install -y {apt[tool_key]}"
    return None


@bot.callback_query_handler(func=lambda call: call.data == "install_info")
def install_info_callback(call):
    bot.answer_callback_query(call.id)
    missing = [
        (k, v) for k, v in SECURITY_TOOLS.items()
        if not tool_installed(v["binary"])
    ]

    text = "📦 <b>تثبيت الأدوات</b>\n\n"
    text += (
        "لا أنفذ تثبيت عشرات الأدوات أو أوامر النظام تلقائياً من داخل البوت. "
        "بدلاً من ذلك، أعرض أوامر التثبيت المناسبة لتشغيلها على جهازك ومراجعتها أولاً.\n\n"
    )

    shown = 0
    for key, info in missing:
        cmd = install_command_for(key)
        if cmd:
            text += f"<b>{info['title']}</b>\n<code>{cmd}</code>\n\n"
            shown += 1
            if shown >= 12:
                break

    if shown == 0:
        text += "لا توجد أوامر تثبيت جاهزة لهذه الأدوات؛ بعضها يحتاج تثبيتاً خاصاً أو Docker/Go/Python."

    bot.send_message(call.message.chat.id, text)


# Add status/install controls to the security menu.
_original_security_menu = security_menu

def security_menu(user_id):
    kb = _original_security_menu(user_id)
    kb.row(
        types.InlineKeyboardButton("⚙️ حالة الأدوات", callback_data="tools_status"),
        types.InlineKeyboardButton("📦 أوامر التثبيت", callback_data="install_info"),
    )
    return kb


# ---------------- Run ----------------

if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.infinity_polling(skip_pending=True)
