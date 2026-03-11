from functools import wraps
from flask import session, redirect, url_for, current_app, request

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_group' in session:
            return func(*args, **kwargs)
        else:
            return redirect(url_for('bp_auth.auth_handler'))
    return wrapper



def group_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_group' in session:
            access = current_app.config['db_access']
            user_request = request.endpoint.split('.')[0] # Имя blueprint
            #print('request.endpoint=', request.endpoint)
            #print('user_request=', user_request)
            user_role = session.get('user_group')
            if user_role in access and user_request in access[user_role]:
                return func(*args, **kwargs)
            else:
                return 'У вас нет прав на эту функциональность'
        return 'Необходимо авторизоваться'
    return wrapper