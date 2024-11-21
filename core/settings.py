from environs import Env

env = Env()  # Создаем экземпляр класса Env
env.read_env()  # Методом read_env() читаем файл .env и загружаем из него переменные в окружение

bot_token = env('BOT_TOKEN')
openai_key = env('OPENAI_KEY')
course_api_key = env('COURSE_API_KEY')
model_api_url = env('MODEL_API_URL')
search_api_key = env('SEARCH_API_KEY')