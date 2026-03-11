from functools import wraps
from flask import session, redirect, url_for, current_app, request

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        return redirect(url_for('blueprint_auth.login'))
    return wrapper

def role_required(*roles):
    """Check if the logged-in user has one of the required roles"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'role' in session and session['role'] in roles:
                return func(*args, **kwargs)
            return '<p>У вас нет прав на эту функциональность</p> <a href="/">Главное меню</a>'
        return wrapper
    return decorator
