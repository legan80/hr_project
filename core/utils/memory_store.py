# memory_store.py
from langchain.memory import ConversationBufferWindowMemory

# определяем общий словарь пользователей
user_memories = {}

# функция для получения/создания памяти
def get_user_memory(user_id):
    if user_id not in user_memories:
        user_memories[user_id] = ConversationBufferWindowMemory(
            memory_key='history',
            k=5,
            input_key='question'
        )
    return user_memories[user_id]
