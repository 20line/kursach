import os

from flask import Blueprint, render_template, redirect, url_for, session, request

from database.add_order import add_order
from database.sql_provider import SQLProvider
from model_route import model_route

blueprint_order = Blueprint('bp_order', __name__, template_folder='templates')
provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))


@blueprint_order.route('/', methods=['GET'])
def show_products():
    """Отображает список доступных услуг и содержимое корзины."""
    session.modified = True
    basket = session.get('basket', {})
    items = model_route(provider, {}, 'service_list.sql')
    return render_template('basket_order_list.html', items=items.result, basket=basket)


@blueprint_order.route('/', methods=['POST'])
def prod_to_basket():
    """Обрабатывает добавление услуги в корзину."""
    if 'basket' not in session:
        session['basket'] = {}

    prod_id = request.form.get('prod_id')
    if not prod_id:
        # Нет идентификатора – ничего не делаем
        return redirect(url_for('bp_order.show_products'))

    # Получаем данные об услуге из БД
    result_info = model_route(provider, request.form, 'get_service.sql')
    if not result_info.result:
        # Услуга не найдена – возможно, удалена
        return redirect(url_for('bp_order.show_products'))

    prod_name, prod_price = result_info.result[0]

    # Добавляем или обновляем позицию в корзине
    if prod_id in session['basket']:
        session['basket'][prod_id]['amount'] += 1
    else:
        session['basket'][prod_id] = {
            'prod_name': prod_name,
            'prod_price': prod_price,
            'amount': 1
        }

    session.modified = True
    return redirect(url_for('bp_order.show_products'))


@blueprint_order.route('/create_order')
def create_order():
    """Оформляет заказ (создаёт запись в booking и booking_detail)."""
    basket = session.get('basket', {})
    if not basket:
        return render_template('create_order.html', basket=basket, message='Корзина пуста')

    # В реальном проекте здесь должен быть ID текущего клиента из сессии
    # Для теста используем фиксированного клиента с ID=1
    user_id = 1
    result_message = add_order(provider, [user_id])
    session.pop('basket', None)  # очищаем корзину после оформления
    return render_template('create_order.html', basket=basket, message=result_message)


@blueprint_order.route('/clear')
def clear_basket():
    """Полностью очищает корзину."""
    session.pop('basket', None)
    return redirect(url_for('bp_order.show_products'))