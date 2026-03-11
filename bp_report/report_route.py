import os
from flask import Blueprint, render_template, request

from access import login_required, group_required
from database.sql_provider import SQLProvider
from model_route import model_route

blueprint_report = Blueprint('bp_report', __name__, template_folder='templates')
provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))

@blueprint_report.route('/', methods=['GET'])
@login_required
@group_required
def report_menu_handle():
    return render_template('report_menu.html')

@blueprint_report.route('/create', methods=['GET'])
@login_required
@group_required
def create_report_handle():
    return render_template('create_report.html')

@blueprint_report.route('/create', methods=['POST'])
def create_report_form():
    user_input = request.form
    year, month = user_input['year'], user_input['month']
    if year.isdigit() and month.isdigit():
        if not(int(month) in range(1, 13)):
            message = 'Значение месяца не входит в допустимый диапазон'
            return render_template('create_report.html', message=message)

        message = model_route(provider, user_input, 'create_report.sql').result[0][0]
    else:
        message = 'Неверные значения месяца или года'

    return render_template('create_report.html', message=message)


@blueprint_report.route('/show', methods=['GET'])
@login_required
@group_required
def show_report_handle():
    return render_template('show_report.html')

@blueprint_report.route('/show', methods=['POST'])
def show_report_form():
    user_input = request.form
    year, month = user_input['year'], user_input['month']
    if year.isdigit() and month.isdigit():
        if not(int(user_input['month']) in range(1, 13)):
            message = 'Значение месяца не входит в допустимый диапазон'
            return render_template('create_report.html', message=message)

        result_info = model_route(provider, user_input, 'get_report.sql')
        if result_info.status:
            reports = result_info.result
            prod_title = 'Результат от model_route'
            return render_template('dynamic.html', prod_title=prod_title, products=reports, columns=['Id отчёта', 'Количество проданных продуктов', 'Общая выручка'])
        else:
            message = 'Отчёта за указанный период не существует'
    else:
        message = 'Неверные значения месяца или года'
    return render_template('create_report.html', message=message)

@blueprint_report.route('/top', methods=['GET'])
@login_required
@group_required
def top_services_form():
    return render_template('top_services_form.html')

@blueprint_report.route('/top', methods=['GET'])
@login_required
@group_required
def top_service_form():
    return render_template('top_service_form.html')

@blueprint_report.route('/top', methods=['POST'])
def top_service_result():
    month = request.form.get('month')
    year = request.form.get('year')
    try:
        month = int(month)
        year = int(year)
        if not (1 <= month <= 12):
            raise ValueError
    except (ValueError, TypeError):
        message = 'Некорректный месяц или год'
        return render_template('top_service_form.html', message=message)

    result_info = model_route(provider, {'month': month, 'year': year}, 'top_services.sql')
    if result_info.status and result_info.result:
        # Для одной строки тоже подойдет dynamic.html, но можно создать отдельный шаблон.
        # Используем dynamic.html, передавая список с одним элементом.
        return render_template('dynamic.html',
                               prod_title=f'Самая популярная услуга в {month}/{year}',
                               products=result_info.result,
                               columns=['Услуга', 'Количество', 'Выручка'])
    else:
        message = 'Нет данных за указанный период'
        return render_template('top_services_form.html', message=message)