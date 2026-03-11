import os
from flask import Blueprint, render_template, request

from access import login_required, group_required
from database.sql_provider import SQLProvider
from model_route import model_route

blueprint_query = Blueprint('bp_query', __name__, template_folder='templates')
provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql'))

@blueprint_query.route('/', methods=['GET'])
@login_required
@group_required
def product_handle():
    return render_template('query_menu.html')

@blueprint_query.route('/', methods=['POST'])
def product_result_handler():
    user_input = request.form
    result_info = model_route(provider, user_input)
    if result_info.status:
        products = result_info.result
        prod_title = 'Результат от model_route'
        return render_template('dynamic.html', prod_title=prod_title, products=products, columns=['Название', 'Единица измерения', 'Стоимость'])
    else:
        return 'Что-то пошло не так'