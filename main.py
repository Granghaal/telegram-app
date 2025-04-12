from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
import json
import os

from config import BOT_TOKEN, ADMIN_USERNAMES
from functions import get_active_tasks, save_task, load_tasks

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.answer("✅ Бот работает! Напиши /webapp чтобы открыть интерфейс задач.")

@dp.message_handler(commands=["webapp", "web"])
async def open_webapp(message: types.Message):
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton(
            text="Открыть интерфейс задач 🧩",
            web_app=WebAppInfo(url="https://granghaal.github.io/telegram-app/")  # Замени на свою ссылку
        )
    )
    await message.answer("Нажми кнопку ниже, чтобы открыть интерфейс:", reply_markup=keyboard)

@dp.message_handler(commands=["планерка"])
async def send_task_summary(message: types.Message):
    if message.from_user.username not in ADMIN_USERNAMES:
        await message.reply("⛔ Только для администратора.")
        return

    tasks = get_active_tasks()
    text = "📂 Актуальные задачи:\n"

    if not tasks:
        text += "✅ Все задачи выполнены!"
    else:
        for t in tasks:
            deadline = t.get("deadline", "не указано")
            priority = t.get("priority", "обычный")
            category = t.get("category", "без категории")
            author = t.get("author", "неизвестен")
            title = t.get("title", "без названия")
            text += f"\n• {title} — 📁 {category} 🔴 {priority} ⏰ {deadline} 🧑‍💼 {author}"

    await message.answer(text)

@dp.message_handler(content_types=types.ContentType.WEB_APP_DATA)
async def receive_webapp_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        save_task(data)
        await message.answer("✅ Задача получена и сохранена.")
    except Exception as e:
        await message.answer(f"❌ Ошибка при сохранении: {e}")

if __name__ == "__main__":
    print("✅ Бот запущен. Ожидаем команды...")
    executor.start_polling(dp, skip_updates=True)
