from core.settings import bot_token

from core.utils.rag import chat_bot
from core.utils.matching import vacancy_resume_matching

from core.keyboards.menu import set_main_menu
from lexicon.lexicon_ru import help_text_ru, services_text_ru

from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import ContentType, Document

import os
import csv
from datetime import datetime

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

# Создаём бота и диспетчер
bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()

# Настраиваем кнопку Menu
@dp.startup()
async def main():
    await set_main_menu(bot)

# Обработчик команды /start
@dp.message(CommandStart())
async def start_command(message: Message):
    await message.answer("Привет 👋\nОтправьте ссылку на вакансию с hh.ru и после файл резюме в формате PDF.\nИли просто задайте мне вопрос из карьерного трека.")
    # await message.answer(f"Привет, {message.from_user.first_name}! Выберите действие...",
    #                      reply_markup=get_inline_keyboard())

# @dp.callback_query(F.data.in_(['resume_analysis', 'chat_with_bot']))
# async def process_buttons_press(callback: CallbackQuery):
#     await callback.answer()

# Этот хэндлер будет срабатывать на команду "/help"
@dp.message(Command(commands='help'))
async def process_help_command(message: Message):
    await message.answer(
        text=help_text_ru)

# Этот хэндлер будет срабатывать на команду "/consult"
@dp.message(Command(commands='consult'))
async def process_help_command(message: Message):
    await message.answer(
        text=services_text_ru, parse_mode='Markdown')

# Проверка ссылки
@dp.message(F.text.startswith("https://hh.ru"))
async def handle_hh_link(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    datetime_utc = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    user_data[user_id] = {"url": message.text.strip(), "username": username, "datetime_utc": datetime_utc}
    await message.reply("Ссылка принята 👍 Теперь отправьте PDF-файл с резюме. Размер файла не должен превышать 2 Мб.")

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
        await message.reply("Ошибка: файл слишком большой 😲 Максимальный размер файла — 2 Мб.")
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
        result = await vacancy_resume_matching(user_id, url, resume)

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

# @dp.message(F.text)
# async def handle_chat_bot(message: Message):
#     query = message.text  # Извлекаем текст сообщения от пользователя
#     answer = chat_bot(query)
#     await message.reply(answer)

# Обработчик сообщений
@dp.message()
async def handle_message(message: Message):
    user_id = message.from_user.id
    user_input = message.text

    # Получаем ответ от модели
    ai_response = chat_bot(user_id, user_input)

    # Отправляем ответ пользователю
    await message.reply(ai_response)

if __name__ == '__main__':
    dp.run_polling(bot)
