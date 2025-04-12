import json
import os
import re
import asyncio
import nest_asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message

nest_asyncio.apply()

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
    match = re.match(r"(\d+)\s+готово", message_text.lower())
    return match.group(1) if match else None

def parse_task_text(text):
    lines = text.strip().split("\n")
    if len(lines) < 4:
        return None
    repeat = lines[4].strip() if len(lines) >= 5 else ""
    return {
        "title": lines[0].strip(),
        "deadline": lines[1].strip(),
        "priority": lines[2].strip().lower(),
        "assignee": lines[3].strip().lower(),
        "repeat": repeat
    }

def get_priority_emoji(priority_text):
    return PRIORITY_MAP.get(priority_text.lower(), "🔘")

def restore_recurring_tasks(tasks):
    today = datetime.now().date().strftime("%d.%m.%Y")
    new_tasks = []
    for t in tasks:
        if t.get("repeat") and t.get("done"):
            if should_repeat_today(t["repeat"]):
                t["done"] = False
                t["id"] = generate_task_id(tasks + new_tasks)
                new_tasks.append(t)
    tasks.extend(new_tasks)
    return tasks

def should_repeat_today(repeat_str):
    today = datetime.now()
    weekday = today.strftime("%A").lower()
    day = today.day
    month = today.month

    if "еженедельно" in repeat_str:
        return weekday in repeat_str
    elif "ежемесячно" in repeat_str:
        return str(day) in repeat_str
    elif "ежеквартально" in repeat_str:
        return str(day) in repeat_str and month in [1, 4, 7, 10]
    return False

# ===== COMMANDS =====
@dp.message(commands=["start"])
async def handle_start(message: Message):
    await message.answer("✅ Бот запущен. Отправь задачу в формате:\n\nНазвание\n11.05.2025\nПриоритет (красный/высокий и т.д.)\n@username\n(опционально) период повторения: ежемесячно 3 числа")

@dp.message(commands=["задачи"])
async def show_tasks(message: Message):
    user = message.from_user.username
    tasks = restore_recurring_tasks(load_tasks())
    tasks = sorted(tasks, key=lambda x: list(PRIORITY_MAP).index(x["priority"]) if x["priority"] in PRIORITY_MAP else 99)
    user_tasks = [t for t in tasks if not t.get("done") and (t["author"] == f"@{user}" or t["assignee"] == f"@{user}")]
    if not user_tasks:
        await message.answer("✅ У вас нет активных задач.")
        return
    text = "📋 Актуальные задачи:\n"
    for t in user_tasks:
        text += f"🔹 {t['id']} — {t['title']} — 📅 {t['deadline']} {get_priority_emoji(t['priority'])} {t['priority']} 👤 {t['assignee']}\n"
    await message.answer(text)

@dp.message()
async def handle_message(message: Message):
    text = message.text.strip()
    user = message.from_user.username
    tasks = load_tasks()

    completed_id = parse_completion(text)
    if completed_id:
        for t in tasks:
            if t["id"] == completed_id:
                t["done"] = True
                save_tasks(tasks)
                await message.answer(f"📦 Задача {completed_id} отправлена в архив.")
                return
        await message.answer("❗Задача не найдена.")
        return

    parsed = parse_task_text(text)
    if not parsed:
        await message.answer("❌ Неверный формат.\nНазвание\n11.05.2025\nПриоритет\n@username\n(опционально) повторение")
        return

    new_task = {
        "id": generate_task_id(tasks),
        "title": parsed["title"],
        "deadline": parsed["deadline"],
        "priority": parsed["priority"],
        "assignee": parsed["assignee"],
        "repeat": parsed["repeat"],
        "author": f"@{user}",
        "done": False
    }
    tasks.append(new_task)
    save_tasks(tasks)
    await message.answer(f"✅ Задача добавлена (ID: {new_task['id']})")

# ===== DAILY REMINDER (OPTIONAL) =====
async def daily_task_reminder():
    settings = load_settings()
    if not settings.get("enabled"):
        return
    now = datetime.now().strftime("%H:%M")
    if now != settings.get("time"):
        return

    tasks = restore_recurring_tasks(load_tasks())
    user_map = {}
    for t in tasks:
        if not t.get("done"):
            key = t["assignee"]
            user_map.setdefault(key, []).append(t)

    for username, user_tasks in user_map.items():
        text = "📋 Ваши задачи на сегодня:\n"
        for t in sorted(user_tasks, key=lambda x: list(PRIORITY_MAP).index(x["priority"]) if x["priority"] in PRIORITY_MAP else 99):
            text += f"🔹 {t['id']} — {t['title']} — 📅 {t['deadline']} {get_priority_emoji(t['priority'])} {t['priority']}\n"
        try:
            await bot.send_message(chat_id=username, text=text)
        except:
            pass

async def scheduler():
    while True:
        await daily_task_reminder()
        await asyncio.sleep(60)

async def main():
    asyncio.create_task(scheduler())
    print("📅 Бот запущен. Ожидаем задачи...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
