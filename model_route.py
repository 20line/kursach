from dataclasses import dataclass
from database.select import select_dict
from database.select2 import select_dict2


@dataclass
class ResultInfo:
    result: tuple
    status: bool
    err_message: str


def model_route(provider, user_input: dict, filename='product.sql'):
    err_message = ''
    _sql = provider.get(filename)

    if filename == 'service_list.sql':
        result = select_dict2(_sql, user_input)
    else:
        result = select_dict(_sql, user_input)

    if result:
        return ResultInfo(result=result, status=True, err_message=err_message)
    else:
        err_message = 'Данные не получены'
        return ResultInfo(result=result, status=False, err_message=err_message)

