import json
import os
import re
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

DATA_FILE = "tasks.json"

# Загружаем задачи из файла
def load_tasks():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# Сохраняем задачи в файл
def save_tasks(tasks):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)

# Генерация уникального ID
def generate_task_id(tasks):
    existing_ids = [int(t["id"]) for t in tasks if "id" in t]
    return str(max(existing_ids) + 1) if existing_ids else "101"

# Проверка готовности задачи
def parse_completion(message_text):
    match = re.match(r"(\d+)\s+готово", message_text.lower())
    return match.group(1) if match else None

# Разбор входящего задания
def parse_task_text(text):
    lines = text.strip().split("\n")
    if len(lines) < 4:
        return None
    return {
        "title": lines[0].strip(),
        "deadline": lines[1].strip(),
        "priority": lines[2].strip(),
        "assignee": lines[3].strip().lower(),
    }

@dp.message_handler(commands=["start"])
async def handle_start(message: types.Message):
    await message.answer("✅ Бот запущен. Просто отправь задачу в формате:\n\nНазвание\n11.05.2025\nКрасный\n@username")

@dp.message_handler()
async def handle_task_message(message: types.Message):
    text = message.text.strip()
    user = message.from_user.username
    tasks = load_tasks()

    # Обработка завершения задачи
    completed_id = parse_completion(text)
    if completed_id:
        updated = [t for t in tasks if t["id"] != completed_id]
        if len(updated) < len(tasks):
            save_tasks(updated)
            await message.answer(f"📦 Задача {completed_id} отправлена в архив.")
        else:
            await message.answer("❗Задача не найдена.")
        return

    # Показ задач по команде
    if text.lower() in ["/задачи", "задачи"]:
        user_tasks = [t for t in tasks if t["author"] == f"@{user}" or t["assignee"] == f"@{user}"]
        if not user_tasks:
            await message.answer("✅ У вас нет активных задач.")
            return
        response = "📋 Актуальные задачи:\n"
        for t in user_tasks:
            response += f"🔹 {t['id']} — {t['title']} — 📅 {t['deadline']} 🟥 {t['priority']} 👤 {t['assignee']}\n"
        await message.answer(response)
        return

    # Обработка новой задачи
    parsed = parse_task_text(text)
    if not parsed:
        await message.answer("❌ Неверный формат. Отправь:\nНазвание\n11.05.2025\nПриоритет\n@username")
        return

    new_task = {
        "id": generate_task_id(tasks),
        "title": parsed["title"],
        "deadline": parsed["deadline"],
        "priority": parsed["priority"],
        "assignee": parsed["assignee"],
        "author": f"@{user}",
    }
    tasks.append(new_task)
    save_tasks(tasks)
    await message.answer(f"✅ Задача добавлена (ID: {new_task['id']})")
