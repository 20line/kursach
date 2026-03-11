from logging import exception

from pymysql import connect
from pymysql.err import OperationalError

# В классе наследуются три метода: init, enter, exit. Это нужно для работы с with, обеспечивает порядок передачи управления
class DBContextManager:
    def __init__(self, db_connect: dict):
        self.conn = None
        self.cursor = None
        self.db_connect = db_connect

    def __enter__(self):
        try:
            self.conn = connect(**self.db_connect)
            self.cursor = self.conn.cursor()
            self.conn.begin() # Точка начала транзакции
            return self.cursor
        except OperationalError as err:
            print(err.args())
            return None

    def __exit__(self, exc_type, exc_val, exc_tb): # При окончании всех действий или при ошибке, сервер передаёт 3 параметра: exc_type - тип ошибки, exc_val - значения
        if exc_type:
            print(exc_type)
            print(exc_val)
        if self.cursor:
            if exc_type:
                self.conn.rollback()
            else:
                self.conn.commit()
            self.cursor.close()
            self.conn.close()
        return True


''' with DBContextManager(...) as cursor: - передаётся управление в метод init (наследуемый), т.к. используется имя класса
Потом автоматом идёт управление в enter после инициализации. cursor - то, что возвращается после enter, если всё в порядке, если не в порядке, то ничего не вернётся.
Если ничего не вернул, то значит вызываем ошибку. Дальше возвращаем управление в тело with'''