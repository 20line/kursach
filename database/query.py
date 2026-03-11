# database/query.py
from flask import current_app
from database.DBcm import DBContextManager
import logging

log = logging.getLogger(__name__)

def execute_sql(sql: str, params=None):
    """
    Универсальная функция для выполнения SQL.
    Логирует сам запрос — теперь мы УВИДИМ, что именно выполняется!
    """
    log.debug(f"Выполняем SQL: {sql.strip()[:200]}{'...' if len(sql.strip()) > 200 else ''}")
    log.debug(f"Параметры: {params}")

    with DBContextManager(current_app.config['db_config']) as cursor:
        if cursor is None:
            log.error("Нет подключения к БД")
            return None

        try:
            cursor.execute(sql, params or ())

            # Определяем тип запроса по первым словам
            query_type = sql.strip().upper().split()[0]

            if query_type in ('SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN'):
                result = cursor.fetchall()
                log.debug(f"SELECT вернул {len(result)} строк")
                return result
            else:
                cursor.connection.commit()
                log.debug(f"INSERT/UPDATE/DELETE: затронуто строк = {cursor.rowcount}")
                return cursor.lastrowid

        except Exception as e:
            log.error(f"Ошибка SQL: {e}")
            cursor.connection.rollback()
            return None