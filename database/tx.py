from contextlib import contextmanager
from pymysql import connect
from flask import current_app
import logging

log = logging.getLogger(__name__)

@contextmanager
def transaction():
    """Простая транзакция: commit при успехе, rollback при любой ошибке"""
    conn = None
    cursor = None
    try:
        conn = connect(**current_app.config['db_config'])
        cursor = conn.cursor()
        conn.begin()
        log.debug("Транзакция начата")
        yield cursor
        conn.commit()
        log.debug("Транзакция успешно закоммичена")
    except Exception as e:
        if conn:
            conn.rollback()
            log.warning("Транзакция откатана из-за ошибки")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()