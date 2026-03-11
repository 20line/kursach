import os
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from access import login_required, role_required
from model_route import model_route
from database.sql_provider import SQLProvider
from database.query import execute_sql
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

import logging
log = logging.getLogger(__name__)

blueprint_report = Blueprint(
    'blueprint_report',
    __name__,
    template_folder='templates'
)

# Инициализация провайдера SQL
provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql_query'))


@blueprint_report.route('/menu')
@login_required
def report_menu_handler():
    role=session['role']
    print(role)
    return render_template('report_menu.html', role=role)

@blueprint_report.route('/menu/most_orders_user', methods=['GET'])
@login_required
def most_orders_user():
    user_sql_file = 'most_orders_user.sql'
    user_input = {}
    columns = ['user_id', 'username', 'booking_count', 'total_revenue']

    log.debug(f"columns: {columns}")

    user_info = model_route(provider, user_input, user_sql_file)
    if not user_info.status or not user_info.result:
        return render_template('most_orders_user.html',
        user={},
        data=[],
        error="Failed to find user with most orders")

    top_user_row = user_info.result[0]
    user = dict(zip(columns, top_user_row))

    log.debug(f"Top user: {user}")

    data_sql_file = 'user_orders.sql'
    order_columns = ['booking_id', 'start_at', 'end_at', 'total_price']
    orders_info = model_route(provider, {'client_id': user['user_id']}, data_sql_file)
    if orders_info.status:
        data = [dict(zip(order_columns, row)) for row in orders_info.result]
    else:
        data = []

    return render_template('most_orders_user.html', user=user, data=data, error="")

@blueprint_report.route('/menu/most_orders_since', methods=['GET', 'POST'])
@login_required
def most_orders_since():
    error = ""
    user = {}
    data = []
    since_date_str = None

    # Default: last 30 days
    default_since = (date.today() - relativedelta(days=30)).isoformat()

    if request.method == 'POST':
        since_date_str = request.form.get('since', '').strip()
    else:
        since_date_str = default_since

    try:
        # Validate date
        since_date = datetime.fromisoformat(since_date_str).date()
        if since_date > date.today():
            raise ValueError("Дата не может быть в будущем")
    except (ValueError, TypeError) as e:
        error = f"Некорректная дата: {str(e)}. Используется значение по умолчанию."
        since_date = date.today() - relativedelta(days=30)
        since_date_str = since_date.isoformat()

    # ─── Get top user ───
    columns = ['user_id', 'username', 'order_count', 'total_items', 'total_weight']
    # after SQL change, this is now:
    columns = ['user_id', 'username', 'booking_count', 'total_revenue']
    params = {'since': since_date_str}

    user_info = model_route(provider, params, 'most_orders_user_since.sql')

    if user_info.status and user_info.result:
        top_row = user_info.result[0]
        user = dict(zip(columns, top_row))
    else:
        error = "Не удалось найти лидера за указанный период (возможно, нет заказов)"
        user = {}

    # ─── Get orders of that user (optional: with same filter) ───
    if user:
        order_columns = ['booking_id', 'start_at', 'end_at', 'total_price']
        
        # Вариант A: фильтруем заказы тем же периодом
        orders_info = model_route(provider, {
            'client_id': user['user_id'],
            'since': since_date_str
        }, 'user_orders_since.sql')
        
        # Вариант B: все заказы пользователя (без фильтра по дате)
        # orders_info = model_route(provider, user['user_id'], 'user_orders.sql')

        if orders_info.status and orders_info.result:
            data = [dict(zip(order_columns, row)) for row in orders_info.result]
        else:
            data = []

    return render_template(
        'most_orders_since.html',
        user=user,
        data=data,
        since=since_date_str,
        default_since=default_since,
        error=error
    )


# ────────────────────────────────
# Отчеты на основе хранимых процедур
# ────────────────────────────────

@blueprint_report.route('/menu/monthly_summary', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def monthly_summary_report():
    rows = None
    month = None
    year = None
    error = ""

    if request.method == 'POST':
        month = request.form.get('month')
        year = request.form.get('year')

        if not month or not year:
            error = "Укажите месяц и год"
        else:
            try:
                month_i = int(month)
                year_i = int(year)
                if not (1 <= month_i <= 12):
                    raise ValueError("Месяц должен быть от 1 до 12")
            except ValueError as e:
                error = f"Некорректные значения месяца/года: {e}"
            else:
                # 1. Запускаем процедуру генерации отчета
                execute_sql(
                    "CALL generate_monthly_bookings_summary(%(month)s, %(year)s);",
                    {"month": month_i, "year": year_i},
                )
                rows = execute_sql(
                    """
                    SELECT report_month, report_year,
                           bookings_cnt, total_revenue
                    FROM report_bookings_monthly_summary
                    WHERE report_month = %(month)s AND report_year = %(year)s
                    """,
                    {"month": month_i, "year": year_i},
                ) or []

    return render_template(
        "report_monthly_summary.html",
        rows=rows,
        month=month,
        year=year,
        error=error,
    )


@blueprint_report.route('/menu/top_clients', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def top_clients_report():
    rows = None
    month = None
    year = None
    error = ""

    if request.method == 'POST':
        month = request.form.get('month')
        year = request.form.get('year')

        if not month or not year:
            error = "Укажите месяц и год"
        else:
            try:
                month_i = int(month)
                year_i = int(year)
                if not (1 <= month_i <= 12):
                    raise ValueError("Месяц должен быть от 1 до 12")
            except ValueError as e:
                error = f"Некорректные значения месяца/года: {e}"
            else:
                execute_sql(
                    "CALL generate_top_clients_by_revenue(%(month)s, %(year)s);",
                    {"month": month_i, "year": year_i},
                )
                rows = execute_sql(
                    """
                    SELECT report_month, report_year,
                           client_id, client_last_name,
                           bookings_cnt, total_revenue, rank_num
                    FROM report_top_clients_by_revenue
                    WHERE report_month = %(month)s AND report_year = %(year)s
                    ORDER BY rank_num
                    """,
                    {"month": month_i, "year": year_i},
                ) or []

    return render_template(
        "report_top_clients.html",
        rows=rows,
        month=month,
        year=year,
        error=error,
    )


@blueprint_report.route('/menu/largest_orders', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def largest_orders_report():
    rows = None
    month = None
    year = None
    error = ""

    if request.method == 'POST':
        month = request.form.get('month')
        year = request.form.get('year')

        if not month or not year:
            error = "Укажите месяц и год"
        else:
            try:
                month_i = int(month)
                year_i = int(year)
                if not (1 <= month_i <= 12):
                    raise ValueError("Месяц должен быть от 1 до 12")
            except ValueError as e:
                error = f"Некорректные значения месяца/года: {e}"
            else:
                execute_sql(
                    "CALL generate_largest_bookings_by_price(%(month)s, %(year)s);",
                    {"month": month_i, "year": year_i},
                )
                rows = execute_sql(
                    """
                    SELECT report_month, report_year,
                           booking_id, client_id,
                           total_price, rank_num,
                           start_at, end_at
                    FROM report_largest_bookings_by_price
                    WHERE report_month = %(month)s AND report_year = %(year)s
                    ORDER BY rank_num
                    """,
                    {"month": month_i, "year": year_i},
                ) or []

    return render_template(
        "report_largest_orders.html",
        rows=rows,
        month=month,
        year=year,
        error=error,
    )