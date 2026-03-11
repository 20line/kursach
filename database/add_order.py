from database.DBcm import DBContextManager
from flask import current_app, session

def add_order(provider, param_list: list) -> str:
    with DBContextManager(current_app.config['db_config']) as cursor:
        if cursor is None:
            raise ValueError('Не удалось подключиться')
        else:
            _sql = provider.get('create_booking.sql')
            cursor.execute(_sql, param_list)
            order_id = cursor.lastrowid

            basket = session.get('basket')
            _sql = provider.get('add_booking_detail.sql')
            order_cost = 0
            for prod_id in basket:
                price = basket.get(prod_id).get('prod_price')
                p_amount = basket.get(prod_id).get('amount')
                order_cost += int(price) * int(p_amount)
                params = [order_id, prod_id, p_amount]
                cursor.execute(_sql, params)
            return f'Заказ №{order_id} успешно добавлен. Сумма заказа: {order_cost}.'
    return 'Ошибка при создании заказа'