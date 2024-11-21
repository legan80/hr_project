from core.settings import search_api_key, course_api_key

from core.utils.utils import ChatOpenAI

from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain.agents import initialize_agent, Tool, AgentType

from langchain.utilities import SerpAPIWrapper

llm_stepik = ChatOpenAI(temperature=0.0, course_api_key=course_api_key)
search_tool = SerpAPIWrapper(serpapi_api_key=search_api_key)

def search_hh(query: str) -> str:
    # Пример функции для поиска на hh.ru
    return search_tool.run(f'{query} site:hh.ru')

hh_tool = Tool(
    name="HH Search",
    func=search_hh,
    description=("""Используй этот инструмент для поиска информации о вакансиях и уровне зарплат на сайте hh.ru.
                 Указывай ключевые слова запроса, относящиеся к вакансиям или резюме."""
    ),
)

tools = [hh_tool]

# Настройка агента
agent_prompt = """Ты карьерный консультант. Твоя задача — отвечать на вопросы пользователей о вакансиях и резюме.
Если не удаётся найти ответ в базе знаний, используй инструмент HH Search для поиска информации на hh.ru.
Всегда предоставляй чёткий и структурированный ответ.

{history}

{context}

Question: {question}
"""
agent_chain = initialize_agent(
    tools=tools,
    llm=llm_stepik,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    prompt=PromptTemplate.from_template(agent_prompt)
)