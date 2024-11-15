from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.types import ContentType, Document
import os

# Импортируем функцию обработки данных
from matching import vacancy_resume_matching

BOT_TOKEN = '8164920416:AAF4hw74uhb7GMV7Q5VjdVV9D9YKRjJ4sPQ'

# Создаём бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Временное хранилище данных для пользователей
user_data = {}

# Обработчик команды /start
@dp.message(CommandStart())
async def start_command(message: Message):
    await message.reply("Привет! Отправьте ссылку на вакансию с hh.ru и файл резюме в формате PDF.")

# Проверка ссылки
@dp.message(F.text.startswith("https://hh.ru"))
async def handle_hh_link(message: Message):
    user_id = message.from_user.id
    user_data[user_id] = {"url": message.text.strip()}
    await message.reply("Ссылка принята. Теперь отправьте PDF-файл с резюме.")

# Проверка PDF-файла
@dp.message(F.document)
async def handle_pdf(message: Message):
    user_id = message.from_user.id

    # Проверяем, что пользователь отправил ссылку ранее
    if user_id not in user_data or "url" not in user_data[user_id]:
        await message.reply("Сначала отправьте ссылку на вакансию с hh.ru.")
        return

    # Проверяем, что файл имеет расширение .pdf
    file_name = message.document.file_name
    if not file_name.endswith(".pdf"):
        await message.reply("Ошибка: требуется файл в формате PDF.")
        return

    # Сохраняем файл
    file_info = await bot.get_file(message.document.file_id)
    file_path = f"temp/{user_id}_{file_name}"
    os.makedirs("temp", exist_ok=True)
    await bot.download_file(file_info.file_path, file_path)
    user_data[user_id]["resume"] = file_path

    # Передаём данные на обработку
    await message.reply("Резюме получено. Обрабатываю данные, подождите...")

    try:
        url = user_data[user_id]["url"]
        resume = user_data[user_id]["resume"]

        # Вызываем функцию обработки
        result = await vacancy_resume_matching(url, resume)

        # Возвращаем результат пользователю
        await message.reply(f"Результат анализа: {result}")
    except Exception as e:
        await message.reply(f"Произошла ошибка обработки: {e}")
    """finally:
        # Удаляем временный файл
        if "resume" in user_data[user_id]:
            os.remove(user_data[user_id]["resume"])
        user_data.pop(user_id, None)"""


if __name__ == '__main__':
    dp.run_polling(bot)