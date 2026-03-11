import os
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from access import login_required, role_required
from model_route import model_route
from database.sql_provider import SQLProvider
from database.tx import transaction

import logging
log = logging.getLogger(__name__)

blueprint_query = Blueprint(
    'blueprint_query',
    __name__,
    template_folder='templates'
)

# Инициализация провайдера SQL
provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql_query'))

@blueprint_query.route('/menu')
@login_required
def query_menu_handler():
    role=session['role']
    print(role)
    return render_template('query_menu.html', role=role)

@blueprint_query.route('/menu/history_client', methods=['GET'])
@login_required
def client_history_handler_form():
    return render_template('client_history_form.html')

@blueprint_query.route('/menu/history', methods=['POST'])
@login_required
def client_history_handler_post():
    username = request.form.get('username', '').strip()

    params = {'username': username}

    sql_file = "history_by_username.sql"
    print(params)
    result_info = model_route(provider, params, sql_file)
    if result_info.status:
        columns = ['booking_id', 'start_at', 'end_at', 'total_price', 'booking_state']
        data = [dict(zip(columns, row)) for row in result_info.result]
        title = "История бронирований клиента"
    else:
        data = []
        title = "Ошибка выполнения запроса"
    return render_template(
        'dynamic.html',
        title=title,
        data=data
    )

# New: List of orders
@blueprint_query.route('/menu/orders_list', methods=['GET'])
@login_required
def orders_list():
    if session['role'] == 'client' and session.get('user_id'):
        sql_file = 'history.sql'  # own bookings
        user_input = {'client_id': session['user_id']}
        columns = ['booking_id', 'start_at', 'end_at', 'total_price', 'booking_state']
        title = "Ваши бронирования"
    else:
        sql_file = 'all_orders.sql'
        user_input = {}
        columns = ['booking_id', 'start_at', 'end_at', 'total_price', 'client_id', 'producer_id', 'booking_state']
        title = "Все бронирования"
    result_info = model_route(provider, user_input, sql_file)
    if result_info.status:
        data = [dict(zip(columns, row)) for row in result_info.result]
    else:
        data = []
        title = "Ошибка выполнения запроса"
    return render_template('dynamic.html', title=title, data=data)

# New: Single order form
@blueprint_query.route('/menu/single_order', methods=['GET'])
@login_required
def single_order_form():
    return render_template('single_order_form.html')

@blueprint_query.route('/menu/find_order', methods=['POST'])
@login_required
def find_order():
    order_id = request.form.get('order_id')
    if order_id and order_id.isdigit():
        return redirect(url_for('blueprint_query.order_detail', order_id=int(order_id)))
    flash("Введите корректный номер бронирования", "warning")
    return redirect(url_for('blueprint_query.single_order_form'))

# New: Single order detail
@blueprint_query.route('/single_order/<int:order_id>', methods=['GET'])
@login_required
def order_detail(order_id):
    params = {'booking_id': order_id}
    sql_file = 'single_order.sql'
    columns = [
        'booking_id', 'start_at', 'end_at', 'room_id',
        'client_id', 'producer_id', 'total_price', 'booking_state'
    ]

    result_info = model_route(provider, params, sql_file)

    if not result_info.status or not result_info.result:
        flash("Бронирование не найдено", "warning")
        return redirect(url_for('blueprint_query.orders_list'))

    order = dict(zip(columns, result_info.result[0]))

    current_role = session.get('role')
    current_user_id = session.get('user_id')

    if current_role == 'client':
        if order['client_id'] != current_user_id:
            flash("Это не ваше бронирование", "danger")
            print("Это не ваше бронирование", "danger")
            return redirect(url_for('blueprint_query.orders_list'))
    
    items_sql = 'order_items.sql'
    items_result = model_route(provider, params, items_sql)

    items = []
    if items_result.status and items_result.result:
        items_columns = ['item_id', 'name', 'price_flat']
        items = [dict(zip(items_columns, row)) for row in items_result.result]

    drivers = []

    return render_template('single_order.html', order=order, items=items, role=current_role, drivers=drivers)

# New: Single order detail
@blueprint_query.route('/single_order', methods=['POST'])
@login_required
def single_order_post():
    user_input = request.form
    order_id = user_input['order_id']
    sql_file = 'single_order.sql'
    input_dict = {'booking_id': order_id}
    columns = [
        'booking_id', 'start_at', 'end_at', 'room_id',
        'client_id', 'producer_id', 'total_price', 'booking_state'
    ]
    result_info = model_route(provider, input_dict, sql_file)
    if result_info.status and result_info.result:
        order = dict(zip(columns, result_info.result[0]))
        items_sql = 'order_items.sql'
        items_result = model_route(provider, input_dict, items_sql)
        if items_result.status:
            items_columns = ['item_id', 'name', 'price_flat']
            items = [dict(zip(items_columns, row)) for row in items_result.result]
        else:
            items = []
        return render_template('single_order.html', order=order, items=items)
    else:
        return render_template('dynamic.html', title="Бронирование не найдено", data=[])