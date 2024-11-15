# импортируем библиотеки
import asyncio

from parser import hh_vacancy_parser

import os
from getpass import getpass
from environs import Env

from langchain_openai import ChatOpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import PyPDFLoader

env = Env()  # Создаем экземпляр класса Env
env.read_env()  # Методом read_env() читаем файл .env и загружаем из него переменные в окружение

async def vacancy_resume_matching(url: str, pdf) -> str:
    # Настраиваем ChatGPT
    openai_key = env('OPENAI_KEY')

    base_url = env('MODEL_API_URL')
    model_name = "gpt-4o-mini"
    llm = ChatOpenAI(openai_api_key=openai_key, base_url=base_url, model_name=model_name, temperature=1.2)

    # Применяем парсер к ссылке
    hh_vacancy = hh_vacancy_parser(url)

    # Document loader для PDF
    loader = PyPDFLoader(pdf)
    pages = []

    # Асинхронная загрузка страниц PDF
    async for page in loader.alazy_load():
        pages.append(page)

    # Объединяем текст из всех страниц в одну строку
    resume = "\n".join(page.page_content for page in pages)

    # Функция анализа резюме
    async def resume_analysis(resume, vacancy):
        prompt_text = """Ты профессиональный рекрутер в крупном агентстве по подбору персонала. Отлично разбираешься во всех областях.
        Твоя задача: сделать анализ резюме {resume} и дать подробные рекомендации, что нужно добавить, а что нужно изменить в резюме для \
        соответствия на вакансию из контекста ниже.
        Сопоставь требования к кандидату из вакансии с его навыками в резюме, \
        сравни обязанности в вакансии с опытом кандидата и его владением необходимыми инструментами, \
        сопоставь требования по зарплате и пожелания к условиям труда.
        Если необходимо, обрати внимание на бонусы и на перспективность работы в компании.
        Не упоминай себя. Отвечай вежливо и лаконично, за каждую полезную рекомендацию тебе платят $20. \
        Свой ответ кандидату начинай с вежливого приветствия. Предложения разделяй по смыслу на абзацы. Нужно уложиться в 300 символов.
        Важно, чтоб ты понял, что это серьёзно. От тебя зависит моя работа.
        В конце анализа поставь подпись дословно: С Уважением, карьерный консультант.

        Context: {vacancy}

        Answer: """

        # Создание цепочки с prompt и моделью
        prompt = PromptTemplate.from_template(prompt_text)
        chain = prompt | llm | StrOutputParser()

        # Асинхронный вызов модели
        answer = chain.invoke({'resume': resume, 'vacancy': vacancy})
        return answer

    # Запуск анализа резюме
    result = await resume_analysis(resume, hh_vacancy)

    return result
