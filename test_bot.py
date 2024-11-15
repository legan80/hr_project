from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types import ContentType
from aiogram import F

#API_URL = 'https://api.telegram.org/bot'
BOT_TOKEN = '8164920416:AAF4hw74uhb7GMV7Q5VjdVV9D9YKRjJ4sPQ'

# Создаем объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Этот хэндлер будет срабатывать на команду "/start"
async def process_start_command(message: Message):
    await message.answer('Привет! Я рекрутер на ИИ.\nПока я только учусь, но\nскоро заработаю в полную силу!')

# Этот хэндлер будет срабатывать на команду "/help"
async def process_help_command(message: Message):
    await message.answer(
        'С моей помощью ты сможешь отредактировать резюме так, '
        'что оно запросто подойдёт под нужную вакансию!'
    )

# Этот хэндлер будет срабатывать на отправку боту фото
async def send_photo_echo(message: Message):
    print(message)
    await message.reply_photo(message.photo[-1].file_id)

# Этот хэндлер будет срабатывать на отправку боту видео
async def send_video_echo(message: Message):
    print(message)
    await message.answer_video(message.video.file_id)

# Этот хэндлер будет срабатывать на отправку боту аудио
async def send_audio_echo(message: Message):
    print(message)
    await message.reply_audio(message.audio.file_id)

# Этот хэндлер будет срабатывать на отправку боту голоса
async def send_voice_echo(message: Message):
    print(message)
    await message.reply_audio(message.voice.file_id)

# Этот хэндлер будет срабатывать на отправку боту стикера
async def send_sticker_echo(message: Message):
    print(message)
    await message.answer_sticker(message.sticker.file_id)

# Этот хэндлер будет срабатывать на отправку боту документов
async def send_doc_echo(message: Message):
    print(message)
    await message.answer_document(message.document.file_id)

# Этот хэндлер будет срабатывать на любые ваши текстовые сообщения,
# кроме команд "/start" и "/help"
async def send_echo(message: Message):
    await message.reply(text=message.text)


# Регистрируем хэндлеры
dp.message.register(process_start_command, Command(commands='start'))
dp.message.register(process_help_command, Command(commands='help'))
dp.message.register(send_photo_echo, F.photo)
dp.message.register(send_video_echo, F.video)
dp.message.register(send_audio_echo, F.audio)
dp.message.register(send_voice_echo, F.voice)
dp.message.register(send_sticker_echo, F.sticker)
dp.message.register(send_doc_echo, F.document)
dp.message.register(send_echo)

if __name__ == '__main__':
    dp.run_polling(bot)