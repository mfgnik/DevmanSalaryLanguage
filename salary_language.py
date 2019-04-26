import requests
import os
from itertools import count
from terminaltables import AsciiTable
from dotenv import load_dotenv


def get_predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    if salary_from:
        return salary_from * 1.2
    if salary_to:
        return salary_to * 0.8


def get_predict_rub_salary_hh(vacancy):
    salary = vacancy['salary']
    if not salary or salary['currency'] != 'RUR':
        return None
    return get_predict_salary(salary['from'], salary['to'])


def get_predict_rub_salary_sj(vacancy):
    return get_predict_salary(vacancy['payment_from'], vacancy['payment_to'])


def find_by_language_on_hh(language):
    return find_by_language(language, 'https://api.hh.ru/vacancies', None,
                               {'text': 'программист {}'.format(language),
                                       'period': 30, 'area': 1}, 'items', 'found', get_predict_rub_salary_hh)


def find_by_language_on_sj(language):
    super_job_key = os.getenv('SECRET_KEY')
    return find_by_language(language, 'https://api.superjob.ru/2.0/vacancies/', {'X-Api-App-Id': super_job_key},
                                {'town': 4, 'catalogues': 48, 'keyword': language}, 'objects', 'total',
                            get_predict_rub_salary_sj)


def find_by_language(language, api_url, headers, params, objects_key, total_key, predict_salary_function):
    vacancies = []
    vacancies_found = 0
    for page in count():
        params['page'] = page
        response = requests.get(api_url, headers=headers,
                                params=params).json()
        if not vacancies_found:
            vacancies_found = response[total_key]
        if objects_key not in response or not response[objects_key]:
            break
        vacancies.extend(response[objects_key])
    vacancies_processed = 0
    average_salary = 0
    for vacancy in vacancies:
        salary = predict_salary_function(vacancy)
        if salary:
            vacancies_processed += 1
            average_salary += salary
    try:
        average_salary //= vacancies_processed
    except ZeroDivisionError:
        pass
    return [language, vacancies_found, vacancies_processed, average_salary]


def construct_table(find_by_language_function):
    languages = ['javascript', 'java', 'python', 'ruby', 'c++', 'c#', 'go', 'scala', 'swift']
    table_data = [['language', 'vacancies_found', 'vacancies_processed', 'average_salary']]
    for language in languages:
        table_data.append(find_by_language_function(language))
    return AsciiTable(table_data).table


if __name__ == '__main__':
    load_dotenv()
    print(construct_table(find_by_language_on_hh))
    print(construct_table(find_by_language_on_sj))
