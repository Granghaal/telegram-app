# NOTE: This code requires Python environment with ssl support for aiogram (via aiohttp).
# If running in a sandbox or limited environment, ensure ssl module is available.

import json
import os
import re
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message

BOT_TOKEN = "7384051613:AAGritfiJRNV_ykW47QgR-q_Lk7qm6kirXs"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DATA_FILE = "tasks.json"
SETTINGS_FILE = "settings.json"

PRIORITY_MAP = {
    "красный": "🔴",
    "высокий": "🔴",
    "оранжевый": "🟠",
    "средний": "🟠",
    "желтый": "🟡",
    "низкий": "🟡",
    "зеленый": "🟢",
    "низший": "🟢"
}

# ===== JSON FILES =====
# ... (без изменений)

# ===== COMMANDS =====
@dp.message(F.text.lower() == "/start")
async def handle_start(message: Message):
    await message.answer(
        "✅ Бот запущен. Просто напишите задачу или используйте формат:\n\n"
        "Название\n11.05.2025\nПриоритет (красный/высокий и т.д.)\n@username\n"
        "(опционально) период повторения: ежемесячно 3 числа"
    )

@dp.message(F.text.lower().startswith("задачи"))
async def show_tasks(message: Message):
    user = message.from_user.username
    text = message.text.strip()
    match = re.match(r"задачи\s+(@\w+)", text.lower())
    target_user = match.group(1).lower() if match else f"@{user}"

    tasks = restore_recurring_tasks(load_tasks())
    tasks = sorted(tasks, key=lambda x: list(PRIORITY_MAP).index(x["priority"]) if x["priority"] in PRIORITY_MAP else 99)
    user_tasks = [t for t in tasks if not t.get("done") and (t["author"] == target_user or t["assignee"] == target_user)]
    if not user_tasks:
        await message.answer(f"✅ Нет активных задач для {target_user}.")
        return
    text = f"📋 Актуальные задачи для {target_user}:\n"
    for t in user_tasks:
        text += f"🔹 {t['id']} — {t['title']} — 📅 {t['deadline']} {get_priority_emoji(t['priority'])} {t['priority']} 👤 {t['assignee']}\n"
    await message.answer(text)

# остальные функции без изменений...
