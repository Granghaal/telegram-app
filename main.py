# NOTE: This code requires Python environment with ssl support for aiogram (via aiohttp).
# If running in a sandbox or limited environment, ensure ssl module is available.

import json
import os
import re
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

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

def get_repeat_dates():
    today = datetime.now()
    return {
        "ежедневно": True,
        "ежемесячно": today.strftime("%d"),
        "ежеквартально": today.strftime("%m-%d") if today.month in [1, 4, 7, 10] else "",
        "еженедельно": today.strftime("%A").lower()
    }

def get_task_keyboard(task_id):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(text="✅ Готово", callback_data=f"done:{task_id}"))
    return kb

# ===== CALLBACK =====
@dp.callback_query(F.data.startswith("done:"))
async def mark_done(callback: CallbackQuery):
    task_id = callback.data.split(":")[1]
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["done"] = True
    save_tasks(tasks)
    await callback.answer("Задача завершена и перемещена в архив.")
    await callback.message.edit_reply_markup(reply_markup=None)

# ===== COMMANDS =====
@dp.message(F.text.lower() == "/start")
async def handle_start(message: Message):
    await message.answer(
        "✅ Бот запущен. Просто напишите задачу или используйте формат:\n\n"
        "Название\n11.05.2025\nПриоритет (красный/высокий и т.д.)\n@username\n"
        "(опционально) еженедельно по вторникам / ежемесячно 3 числа"
    )

@dp.message(F.text.lower().startswith("задачи"))
async def show_tasks(message: Message):
    user = message.from_user.username
    text = message.text.strip()
    match = re.match(r"задачи\\s+(@\\w+)?(.*)?", text.lower())
    target_user = match.group(1).lower() if match and match.group(1) else f"@{user}"
    filter_arg = match.group(2).strip() if match and match.group(2) else ""

    tasks = load_tasks()
    tasks = [t for t in tasks if not t.get("done") and (t["author"] == target_user or t["assignee"] == target_user)]

    if filter_arg:
        if filter_arg in PRIORITY_MAP:
            tasks = [t for t in tasks if t.get("priority", "") == filter_arg]
        else:
            try:
                date_filter = datetime.strptime(filter_arg, "%d.%m.%Y").date()
                tasks = [t for t in tasks if datetime.strptime(t.get("deadline", "01.01.3000"), "%d.%m.%Y").date() == date_filter]
            except:
                pass

    if not tasks:
        await message.answer(f"✅ Нет активных задач для {target_user}.")
        return

    tasks = sorted(tasks, key=lambda x: list(PRIORITY_MAP).index(x["priority"]) if x.get("priority") in PRIORITY_MAP else 99)

    for t in tasks:
        text = f"🔹 {t['id']} — {t['title']} — 📅 {t['deadline']} {get_priority_emoji(t['priority'])} {t['priority']} 👤 {t['assignee']}"
        await message.answer(text, reply_markup=get_task_keyboard(t["id"]))

@dp.message(F.text.lower() == "архив")
async def show_archive(message: Message):
    tasks = load_tasks()
    archived = [t for t in tasks if t.get("done")]
    if not archived:
        await message.answer("📦 Архив пуст.")
        return
    text = "📦 Архив задач:\n"
    for t in archived:
        text += f"☑️ {t['id']} — {t['title']} — 📅 {t['deadline']} {get_priority_emoji(t['priority'])} {t['priority']} 👤 {t['assignee']}\n"
    await message.answer(text)

@dp.message(F.text.lower() == "очистить архив")
async def clear_archive(message: Message):
    tasks = load_tasks()
    tasks = [t for t in tasks if not t.get("done")]
    save_tasks(tasks)
    await message.answer("🧹 Архив очищен.")

@dp.message()
async def handle_general(message: Message):
    text = message.text.strip()
    user = message.from_user.username
    tasks = load_tasks()

    ids_to_archive = parse_completion(text)
    if ids_to_archive:
        for t in tasks:
            if t["id"] in ids_to_archive:
                t["done"] = True
        save_tasks(tasks)
        await message.answer(f"📦 Задачи {' '.join(ids_to_archive)} отправлены в архив.")
        return

    if text.isdigit():
        await message.answer("✏️ Уточните, что нужно обновить (дедлайн/приоритет/assignee)")
        return

    if " — " in text:
        await message.answer("⚙️ Команда не распознана. Проверьте синтаксис.")
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
    await message.answer(f"✅ Задача добавлена (ID: {new_task['id']})", reply_markup=get_task_keyboard(new_task["id"]))

async def main():
    print("🤖 Бот запущен...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
