import json
import os
import re
import asyncio
from datetime import datetime
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


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tasks(tasks):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)


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


def parse_task_update(text):
    lines = text.strip().split("\n")
    if len(lines) >= 2:
        id_line = lines[0].strip()
        updates = {
            "priority": None,
            "deadline": None
        }
        for line in lines[1:]:
            if line.lower() in PRIORITY_MAP:
                updates["priority"] = line.lower()
            elif re.match(r"\d{1,2}[./]\d{1,2}([./]\d{4})?", line):
                updates["deadline"] = line
        return id_line, updates
    return None, None


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
        count = 0
        for t in tasks:
            if t["id"] in ids_to_archive:
                t["done"] = True
                count += 1
        if count > 0:
            save_tasks(tasks)
            await message.answer(f"📦 Задачи {' '.join(ids_to_archive)} отправлены в архив.")
        else:
            await message.answer("❗Задачи не найдены.")
        return

    if "\n" in text:
        lines = text.strip().split("\n")
        if lines[0].isdigit():
            task_id, updates = parse_task_update(text)
            updated = False
            for t in tasks:
                if t["id"] == task_id:
                    if updates["priority"]:
                        t["priority"] = updates["priority"]
                    if updates["deadline"]:
                        t["deadline"] = updates["deadline"]
                    updated = True
            if updated:
                save_tasks(tasks)
                await message.answer(f"🔧 Задача {task_id} обновлена.")
                return

        if len(lines) >= 4:
            new_task = {
                "id": generate_task_id(tasks),
                "title": lines[0],
                "deadline": lines[1],
                "priority": lines[2].lower(),
                "assignee": lines[3].lower(),
                "repeat": lines[4] if len(lines) >= 5 else "",
                "author": f"@{user}",
                "done": False
            }
            tasks.append(new_task)
            save_tasks(tasks)
            await message.answer(f"✅ Задача добавлена (ID: {new_task['id']})")
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


async def main():
    print("🤖 Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
