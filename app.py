# app.py (в корне проекта!)
from flask import Flask, render_template
import os
import json

def create_app():
    app = Flask(__name__)

    # Абсолютные пути — это важно!
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    app.config['db_config'] = json.load(open(os.path.join(BASE_DIR, 'data', 'db_config.json')))
    app.config['db_access'] = json.load(open(os.path.join(BASE_DIR, 'data', 'access.json')))

    app.secret_key = 'super-secret-key-1234567890-change-in-production'

    # Регистрация блюпринтов
    from bp_query.query_route import blueprint_query
    from bp_order.order_route import blueprint_order
    from bp_report.report_route import blueprint_report
    from bp_auth.auth import blueprint_auth
    from access import login_required

    app.register_blueprint(blueprint_auth, url_prefix='/auth')
    app.register_blueprint(blueprint_query, url_prefix='/query')
    app.register_blueprint(blueprint_order, url_prefix='/order')
    app.register_blueprint(blueprint_report, url_prefix='/report')

    @app.route('/')
    @login_required
    def index():
        return render_template('main_menu.html')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)