from os import name
import requests
import fake_useragent
from bs4 import BeautifulSoup
import time
import json

# определяем функцию для парсинга вакансии с hh.ru
def hh_vacancy_parser(url):
    ua = fake_useragent.UserAgent()
    data = requests.get(
        url=url.split('?')[0],
        headers={"user-agent":ua.random}
    )

    if data.status_code != 200:
        return

    soup = BeautifulSoup(data.content.decode('utf-8', 'ignore'), 'lxml')

    # извлекаем наименование должности
    name = soup.find('h1', attrs={'class':'bloko-header-section-1'}).text

    # извлекаем зарплату
    try:
        # Извлечение текста из тега <span> с информацией о зарплате
        salary = soup.find('div', {'data-qa': 'vacancy-salary'}).text.strip()

        # Очистка текста от лишних пробелов и переносов строк
        salary = ' '.join(salary.split())
    except:
        salary = 'не указана'

    # извлекаем тип занятости
    try:
        # Извлечение текста из тега <p> с информацией о занятости
        job_type = soup.find('p', {'data-qa': 'vacancy-view-employment-mode'}).text.strip()

        # Очистка текста от лишних пробелов и переносов строк
        job_type = ' '.join(job_type.split())
    except:
        job_type = 'не указана'

    # извлекаем требуемый опыт
    try:
        experience = soup.find('span', {'data-qa': 'vacancy-experience'}).text.strip()
    except:
        experience = 'не указан'

    # извлекаем наименование работадателя
    try:
        comp_name = soup.find('span', attrs={'class': 'vacancy-company-name'}).text.strip()
    except:
        comp_name = 'не указано'

    # извлекаем описание вакансии
    try:
        #vacancy = soup.find('div', attrs={'class': 'vacancy-section'}).text.strip()
        vacancy_desc = ' '.join(soup.find('div', attrs={'data-qa': 'vacancy-description'}).text.split())
    except:
        vacancy_desc = 'не указано'

    # извлекаем теги навыков
    try:
        skills = [skill.text.replace("\xa0"," ") for skill in soup.find_all("li",attrs={"data-qa":"skills-element"})]
    except:
        skills = []

    # Объединяем информацию о вакансии в одну строку
    hh_vacancy = "\n".join([f"Наименование должности: {name}",
                            f"Зарплата: {salary}",
                            f"Тип занятости: {job_type}",
                            f"Опыт работы: {experience}",
                            f"Наименование компании: {comp_name}",
                            f"Описание вакансии: {vacancy_desc}",
                            f"Навыки: {', '.join(skills) if skills else 'не указаны'}"])

    return hh_vacancy
