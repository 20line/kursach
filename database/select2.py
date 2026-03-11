# Описываем действия, выполняющиеся при запросе
from database.DBcm import DBContextManager
from flask import current_app # Позволяет обратится к глобальным переменным

def select_list2(_sql: str, param_list: list) -> set: # Возвращает кортеж кортежей
    with DBContextManager(current_app.config['db_config']) as cursor:
        if cursor is None:
            raise ValueError('Не удалось подключиться')
        else:
            cursor.execute(_sql, param_list)
            result = cursor.fetchall()
            schema = [] # Список из названий полей
            # После выполнения sql запроса в курсоре сохраняются названия полей в параметре description
            for item in cursor.description:
                schema.append(item[0])
    return result, schema

def select_dict2(_sql: str, user_input: dict) -> tuple:
    user_list = []
    for key in user_input:
        user_list.append(user_input[key])
    #print('user_list={} in dict'.format(user_list))
    result, schema = select_list2(_sql, user_list)
    result_list = []
    for item in result:
        result_list.append((dict(zip(schema, item))))
    return result_list