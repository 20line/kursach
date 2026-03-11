# model_route.py
from database.query import execute_sql

class ResultInfo:
    def __init__(self, status: bool, result):
        self.status = status
        self.result = result  # ← может быть list или int!


def model_route(provider, params, sql_file) -> ResultInfo:
    _sql = provider.get(sql_file)
    result = execute_sql(_sql, params)
    
    print(sql_file)

    if result is None:
        return ResultInfo(False, None)
    
    return ResultInfo(True, result)