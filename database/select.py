# Описываем действия, выполняющиеся при запросе
from database.DBcm import DBContextManager
from flask import current_app # Позволяет обратится к глобальным переменным

def select_list(_sql: str, param_list: list) -> set: # Возвращает кортеж кортежей
    with DBContextManager(current_app.config['db_config']) as cursor:
        if cursor is None:
            raise ValueError('Не удалось подключиться')
        else:
            cursor.execute(_sql, param_list)
            if "INSERT" in _sql:
                result = cursor.lastrowid
            else:
                result = cursor.fetchall()
            return result

def select_dict(_sql: str, user_input: dict) -> tuple:
    user_list = []
    for key in user_input:
        user_list.append(user_input[key])

    result = select_list(_sql, user_list)
    return result