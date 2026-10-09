# Mafia 1 Pro — Starter Project

A modular Telegram bot starter with an isolated assistant package, owner-only controls, safe tool registry, and a virtual-number integration placeholder.

## Requirements
- Python 3.10+
- A Telegram bot token from BotFather
- Your Telegram numeric user ID for owner controls

## Setup
1. Copy `.env.example` to `.env`.
2. Set `BOT_TOKEN` and `OWNER_ID` in `.env`. Never upload `.env` or share your token.
3. Set `AI_API_URL`, `AI_API_KEY`, and `AI_MODEL` using values from your chosen provider's official documentation if you want AI replies. Keep all secrets in `.env`.\n4. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
5. Start the bot:
   ```bash
   python bot.py
   ```

## Project layout
- `bot.py`: Telegram entry point and menu.
- `assistant/`: assistant logic, configuration, memory, security checks, and tool registry.
- `virtual_numbers.py`: safe integration placeholder. It does not buy/rent numbers or receive SMS until a legitimate provider is configured.
- `tools/`: separated modules for future defensive/security and utility features.

## Important
This is a clean, tested starter scaffold—not a hosted AI model or a fully connected virtual-number service. Add provider credentials only through environment variables and implement each provider behind a documented API. Cybersecurity features should only be used on systems you own or are authorized to test.


## AI-assisted defensive cybersecurity
`tools/cybersecurity/` calls the configured AI bridge for defensive explanations and remediation advice. It analyses text you provide; it does not itself run port scans, exploit tests, or claim a system is vulnerable without evidence. Active tools should be added separately, with explicit authorization checks and scoped targets.


## Owner-only project management
Set `OWNER_ID` to your numeric Telegram user ID. The owner can use:
- `/admin` — show management commands
- `/addbutton name | Button label | Description | category` — add a persistent custom menu button
- `/removebutton name` — remove a custom button
- `/newtool name | Description | category` — create a Python tool template under `tools/custom/`
- Upload a `.py` document to the bot — save it under `tools/custom/` after conservative static checks

**Safety boundary:** custom buttons are menu entries only until code is implemented and reviewed. Uploaded Python files are never imported or executed automatically. Static checks cannot prove code is safe. Keep backups and only upload code you understand. The assistant does not autonomously delete source files or execute arbitrary commands.


## Owner project management from Telegram
After setting `OWNER_ID`, the owner can use:
- `/manage list` — list registered menu buttons.
- `/manage addbutton name | label | description | category` — add a menu item.
- `/manage removebutton name` — remove a menu item (does not delete source code).
- `/manage newtool name | description | category` — create a tool template in `tools/custom/`.
- Send a `.py` document to the bot — save a statically checked copy in `tools/custom/` for manual review.

**Safety boundary:** uploaded/generated Python is never imported or executed automatically. Static checks are not a sandbox. A button/catalog entry does not make a real tool functional; implementation, code review, testing, and a deliberate integration step are still required. Menu changes are restricted to the configured owner.
