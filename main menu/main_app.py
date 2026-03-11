import json
from flask import Flask, render_template, session

from access import login_required
from bp_auth.auth import blueprint_auth
from bp_query.query_route import blueprint_query
from bp_report.report_route import blueprint_report
from basket.order_route import blueprint_order

app = Flask(__name__)

with open('../data/db_config.json') as f: # Считываем файл в переменную f
    app.config['db_config'] = json.load(f) # Добавляем ключ в конфиг

with open('../data/access.json') as f:
    app.config['db_access'] = json.load(f)

app.register_blueprint(blueprint_query, url_prefix='/query')
app.register_blueprint(blueprint_auth, url_prefix='/auth')
app.register_blueprint(blueprint_report, url_prefix='/report')
app.register_blueprint(blueprint_order, url_prefix='/order')

app.secret_key = 'my secret key'


@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/exit')
def system_exit():
    return render_template('exit.html')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5002, debug=True)