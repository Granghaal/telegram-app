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
dp = Dispatcher(bot=bot)

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
def load_tasks():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_tasks(tasks):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

# ===== HELPERS =====
def generate_task_id(tasks):
    existing_ids = [int(t["id"]) for t in tasks if "id" in t]
    return str(max(existing_ids) + 1) if existing_ids else "101"

def parse_completion(message_text):
    match = re.findall(r"\b(\d+)\b", message_text.lower())
    if "готово" in message_text.lower() and match:
        return match
    return []

def get_priority_emoji(priority_text):
    return PRIORITY_MAP.get(priority_text.lower(), "🔘")

# ===== COMMANDS =====

async def main():
    print("🤖 Бот запущен...")
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
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

    tasks = load_tasks()
    tasks = sorted(tasks, key=lambda x: list(PRIORITY_MAP).index(x["priority"]) if x.get("priority") in PRIORITY_MAP else 99)
    user_tasks = [t for t in tasks if not t.get("done") and (t["author"] == target_user or t["assignee"] == target_user)]
    if not user_tasks:
        await message.answer(f"✅ Нет активных задач для {target_user}.")
        return
    text = f"📋 Актуальные задачи для {target_user}:\n"
    for t in user_tasks:
        text += f"🔹 {t['id']} — {t['title']} — 📅 {t['deadline']} {get_priority_emoji(t['priority'])} {t['priority']} 👤 {t['assignee']}\n"
    await message.answer(text)

@dp.message()
async def handle_general(message: Message):
    text = message.text.strip()
    user = message.from_user.username
    tasks = load_tasks()

    ids_to_archive = parse_completion(text)
    if ids_to_archive:
        updated = [t for t in tasks if t["id"] not in ids_to_archive]
        archived = [t for t in tasks if t["id"] in ids_to_archive]
        if archived:
            for t in archived:
                t["done"] = True
            save_tasks(tasks)
            await message.answer(f"📦 Задачи {' '.join(ids_to_archive)} отправлены в архив.")
        else:
            await message.answer("❗Задачи не найдены.")
        return

    new_task = {
        "id": generate_task_id(tasks),
        "title": text,
        "deadline": "не указано",
        "priority": "обычный",
        "assignee": f"@{user}",
        "repeat": "",
        "author": f"@{user}",
        "done": False
    }
    tasks.append(new_task)
    save_tasks(tasks)
    await message.answer(f"✅ Задача добавлена (ID: {new_task['id']})")
