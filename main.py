from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.types import ContentType, Document
import os
from environs import Env
import csv
from datetime import datetime

# Импортируем функцию обработки данных
from matching import vacancy_resume_matching

env = Env()  # Создаем экземпляр класса Env
env.read_env()  # Методом read_env() читаем файл .env и загружаем из него переменные в окружение

BOT_TOKEN = env('BOT_TOKEN')

# Создаём бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Путь к папке для сохранения данных
DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)
# Путь к файлу истории
HISTORY_FILE = os.path.join(DATA_FOLDER, "history.csv")

# Проверяем, существует ли файл истории, если нет — создаём и добавляем заголовки
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["user_id", "username", "datetime_utc", "vacancy_url", "resume_file", "response_file"])

# Временное хранилище данных для пользователей
user_data = {}

# Обработчик команды /start
@dp.message(CommandStart())
async def start_command(message: Message):
    await message.reply("Привет! Отправьте ссылку на вакансию с hh.ru и после файл резюме в формате PDF.")

# Проверка ссылки
@dp.message(F.text.startswith("https://hh.ru"))
async def handle_hh_link(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    datetime_utc = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    user_data[user_id] = {"url": message.text.strip(), "username": username, "datetime_utc": datetime_utc}
    await message.reply("Ссылка принята. Теперь отправьте PDF-файл с резюме. Размер файла не должен превышать 2 Мб.")

# Проверка PDF-файла
@dp.message(F.document)
async def handle_pdf(message: Message):
    user_id = message.from_user.id

    # Проверяем, что пользователь отправил ссылку ранее
    if user_id not in user_data or "url" not in user_data[user_id]:
        await message.reply("Сначала отправьте ссылку на вакансию с hh.ru.")
        return

    # Извлекаем данные пользователя
    username = user_data[user_id].get("username", "Unknown")  # Извлекаем username
    datetime_utc = user_data[user_id].get("datetime_utc")  # Извлекаем время

    # Проверяем, что файл имеет расширение .pdf
    file_name = message.document.file_name
    if not file_name.endswith(".pdf"):
        await message.reply("Ошибка: требуется файл в формате PDF.")
        return

    # Проверяем размер файла (допустимо не более 2 МБ)
    file_size_limit = 2 * 1024 * 1024  # 2 МБ в байтах
    if message.document.file_size > file_size_limit:
        await message.reply("Ошибка: файл слишком большой. Максимальный размер файла — 2 Мб.")
        return

    # Сохраняем файл резюме
    file_info = await bot.get_file(message.document.file_id)
    resume_file_path = os.path.join(DATA_FOLDER, f"{user_id}_{datetime_utc}_{file_name}")
    await bot.download_file(file_info.file_path, resume_file_path)
    user_data[user_id]["resume"] = resume_file_path

    # Передаём данные на обработку
    await message.reply("Резюме получено. Анализирую полученные данные, подождите...")

    try:
        url = user_data[user_id]["url"].split("?")[0]
        resume = user_data[user_id]["resume"]

        # Вызываем функцию обработки
        result = await vacancy_resume_matching(url, resume)

        # Сохраняем результат анализа в файл
        response_file_path = os.path.join(DATA_FOLDER, f"{user_id}_{datetime_utc}_response.txt")
        with open(response_file_path, mode="w", encoding="utf-8") as response_file:
            response_file.write(result)

        # Записываем данные в CSV
        with open(HISTORY_FILE, mode="a", newline="", encoding="utf-8") as history_file:
            writer = csv.writer(history_file)
            writer.writerow([user_id, username, datetime_utc, url, resume_file_path, response_file_path])

        # Возвращаем результат пользователю
        await message.reply(f"Результат анализа: {result}")
    except Exception as e:
        await message.reply(f"Произошла ошибка обработки: {e}")


if __name__ == '__main__':
    dp.run_polling(bot)
