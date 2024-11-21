from core.settings import (
    openai_key,
    model_api_url,
    search_api_key,
    course_api_key
    )

from core.utils.memory_store import user_memories, get_user_memory
from core.utils.agents import search_hh, tools, agent_chain
import os

#from langchain_openai import ChatOpenAI
#from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.embeddings import HuggingFaceEmbeddings

from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain.vectorstores import FAISS
from langchain.memory import ConversationBufferWindowMemory
from langchain.agents import initialize_agent, Tool, AgentType

from langchain.utilities import SerpAPIWrapper

search_tool = SerpAPIWrapper(serpapi_api_key=search_api_key)

# openai_key = openai_key
# model_name="gpt-4o-mini"
# llm = ChatOpenAI(openai_api_key=openai_key, base_url=model_api_url, model_name=model_name, temperature=1.2)

from core.utils.utils import ChatOpenAI
llm_stepik = ChatOpenAI(temperature=0.0, course_api_key=course_api_key)

# ##########################################
# ##########################################
# def load_all_texts_from_folder(folder_path):
#     """
#     Читает содержимое всех файлов *.txt в указанной папке, объединяет их в одну строку
#     и заменяет неразрывные пробелы на обычные пробелы.

#     :param folder_path: Путь к папке, содержащей текстовые файлы.
#     :return: Строка с объединённым содержимым всех файлов.
#     """
#     doc = ""
#     for file_name in os.listdir(folder_path):
#         # Проверяем, является ли файл текстовым
#         if file_name.endswith(".txt"):
#             file_path = os.path.join(folder_path, file_name)
#             with open(file_path, encoding="utf-8") as f:
#                 text = f.read()
#                 # Заменяем неразрывные пробелы на обычные
#                 text = text.replace("\xa0", " ")
#                 # Удаляем символы '#' и '*'
#                 text = text.replace("#", "").replace("*", "")
#                 doc += text + "\n"  # Добавляем текст и разделитель
#     return doc

# # Использование функции
# folder_path = "./datasets/txt"
# doc = load_all_texts_from_folder(folder_path)
# ##########################################

# ######### SPLITTER #######################
# ##########################################
# splitter = RecursiveCharacterTextSplitter(
# chunk_size=1000,
# chunk_overlap=150,
# length_function=len,
# )
# split_documents = splitter.create_documents([doc])
# bm25 = BM25Retriever.from_documents(split_documents)  # Эмбеддинги ему не нужны
# bm25.k = 5  # Так можно задать количество возвращаемых документов

# ##########################################

# # определяем словарь пользователей
# user_memories = {}

# # функция для получения/создания памяти для пользователя
# def get_user_memory(user_id):
#     if user_id not in user_memories:
#         # создаем память для нового пользователя
#         user_memories[user_id] = ConversationBufferWindowMemory(
#             memory_key='history',
#             k=6,
#             input_key='question'
#         )
#     return user_memories[user_id]


# функция для работы базы знаний
def chat_bot(user_id: int, query: str) -> str:

    # получаем память пользователя
    user_memory = get_user_memory(user_id)
    print(user_memory)

    # определяем модель для эмбеддингов
    # если у вас нет видеокарты, укажите 'device': 'cpu'
    hf_embeddings_model = HuggingFaceEmbeddings(
        model_name="cointegrated/LaBSE-en-ru", model_kwargs={"device": "cpu"}
    )

    # подключаем базу знаний из векторного хранилища
    db = FAISS.load_local(
        "./core/db/faiss_db", hf_embeddings_model, allow_dangerous_deserialization=True
        )

    # ### Определим 🎣 Retriever
    # инициализируем ретривер
    retriever = db.as_retriever(
        search_type="similarity",  # тип поиска похожих документов
        k=30,  # количество возвращаемых документов (Default: 4)
        score_threshold=None,  # минимальный порог для поиска "similarity_score_threshold"
    )

    # ensemble_retriever = EnsembleRetriever(
    #         retrievers=[bm25, retriever],  # список ретриверов
    #         weights=[
    #             0.4,
    #             0.6,
    #         ],  # веса, на которые домножается скор документа от каждого ретривера
    # )

    # template = """You're a career counseling specialist. Your job is to answer candidates' questions and advise on the career track.
    # Answer concisely and in the same language. Separate text into paragraphs, if necessary.
    # Answer the question based only on the following context.
    # If the context doesn't answer the question, answer verbatim 'К сожалению, я не смог найти информацию по вашему запросу.'

    # {history}

    # {context}

    # Question: {question}
    # """

    # простой шаблон с инструкцией с поддержкой истории
    template = """You're a career counseling specialist. Your job is to answer candidates' questions and advise on the career track only.
    Answer concisely and in the same language. Separate text into paragraphs, if necessary.
    Don't use the pretrained data you were trained on to answer.
    If you don't know the answer to a question, answer 'К сожалению, я не смог найти информацию по вашему запросу.'.
    Answer the question based only on the following context:

    {history}

    {context}

    Question: {question}
    """
    # создаём промпт из шаблона
    prompt = PromptTemplate.from_template(template)


    # объявляем функцию, которая будет собирать строку из полученных документов
    def format_docs(docs):
        return "\n\n".join([d.page_content for d in docs])

    # создаём цепочку
    chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
            "history": lambda _: user_memory,
        }
        | prompt
        | llm_stepik
        | StrOutputParser()
    )

    # получаем ответ
    answer = chain.invoke(query)

    # Если база знаний не даёт результата, используем агента
    if "К сожалению, я не смог найти информацию по вашему запросу." in answer:
        try:
            # Агент автоматически решит, использовать ли инструмент HH Search
            agent_answer = agent_chain.run(input=query, memory=user_memory)
            if agent_answer:
                answer = agent_answer
            else:
                raise ValueError("Инструмент HH Search не вернул результат.")
        except Exception as e:
            print(f'Ошибка агента: {e}')
            answer = "К сожалению, я не смог найти дополнительную информацию по вашему запросу."

    # Обновляем память пользователя
    user_memory.save_context({"question": query}, {"output": answer})

    # if "К сожалению, я не смог найти информацию по вашему запросу." in answer:
    #     try:
    #         # Функция для обработки поиска с помощью SerpAPI
    #         serp_context = search_tool.run(f'{query} site:hh.ru')
    #         print(serp_context)

    #         if not serp_context:  # Проверяем, если контекст пустой
    #             raise ValueError("SerpAPI вернул пустой результат.")

    #         serp_chain = (
    #             {
    #                 "context": lambda _: serp_context,
    #                 "question": RunnablePassthrough(),
    #                 "history": lambda _: user_memory,
    #             }
    #             | prompt
    #             | llm_stepik
    #             | StrOutputParser()
    #         )
    #         answer = serp_chain.invoke(query)

    #     except Exception as e:
    #         print(f'Ошибка serp: {e}')
    #         return "К сожалению, я не смог найти дополнительную информацию по вашему запросу."

    # обновляем память
    user_memory.save_context({"question": query}, {"output": answer})

    return answer