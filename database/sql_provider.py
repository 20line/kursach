import os


class SQLProvider:
    def __init__(self, file_path):
        """
        :param file_path: директория, в которой лежат все файлы
        """
        self.scripts = {} # инициализируем словарь
        for file in os.listdir(file_path): # Цикл по всем файлам во входной директории
            _sql = open(f'{file_path}/{file}').read() # Открываем каждый файл
            self.scripts[file] = _sql

    def get(self, file):
        _sql = self.scripts[file]
        return _sql