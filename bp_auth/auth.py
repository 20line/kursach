# bp_auth/auth.py
import os
import logging
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from database.sql_provider import SQLProvider
from model_route import model_route
from flask_bcrypt import Bcrypt
from access import login_required, role_required
from datetime import datetime

log = logging.getLogger(__name__)
bcrypt = Bcrypt()

blueprint_auth = Blueprint('blueprint_auth', __name__, template_folder='templates')
provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql_auth'))

@blueprint_auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('auth.html')

    username = request.form['username']
    password = request.form['password']

    result_info = model_route(provider, {'username': username}, 'auth.sql')

    if not result_info.status or not result_info.result:
        flash('Неверный логин или пароль', 'danger')
        return render_template('auth.html')

    user = result_info.result[0]  # (user_id, username, password_hash, role)
    stored_hash = user[2]

    if not bcrypt.check_password_hash(stored_hash, password):
        flash('Неверный логин или пароль', 'danger')
        return render_template('auth.html')

    # УСПЕШНЫЙ ЛОГИН — сохраняем всё нужное
    session['user_id'] = user[0]
    session['username'] = user[1]
    session['role'] = user[3]

    # Для клиента и сотрудника — их "рабочий" ID = user_id
    if user[3] == 'client':
        session['client_id'] = user[0]   # ← теперь это user_id!
    elif user[3] == 'staff':
        session['staff_id'] = user[0]

    log.info(f"Успешный вход: {username} | роль: {user[3]} | user_id: {user[0]}")
    return redirect(url_for('index'))

@blueprint_auth.route('/logout')
def logout():
    username = session.get('username', 'unknown')
    session.clear()
    log.info(f"Выход пользователя: {username}")
    return redirect(url_for('blueprint_auth.login'))

# ------------------ Registration ------------------

# ─── Public registration ─── (only clients)
@blueprint_auth.route('/register', methods=['GET', 'POST'])
def register_client():
    if request.method == 'GET':
        log.info("Открыта форма регистрации клиента")
        return render_template('register_client.html')   # ← separate template recommended

    log.info("=== ПОПЫТКА РЕГИСТРАЦИИ КЛИЕНТА ===")
    log.debug(f"Все данные формы: {dict(request.form)}")

    try:
        username = request.form['username'].strip()
        email    = request.form['email'].strip()
        password = request.form['password']
        role     = 'client'   # ← жёстко фиксируем!

        # Optional: check honeypot or captcha here in future

        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        user_params = {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'role': role
        }

        result_user = model_route(provider, user_params, 'register_user.sql')
        if not result_user.status or result_user.result == 0:
            log.error("Логин или email уже заняты")
            flash('Логин или email уже заняты', 'danger')
            return redirect(url_for('blueprint_auth.register_client'))

        # Получаем user_id
        user_id_result = model_route(provider, {'username': username}, 'get_user_id.sql')
        if not user_id_result.status or not user_id_result.result:
            flash('Внутренняя ошибка системы', 'danger')
            return redirect(url_for('blueprint_auth.register_client'))

        user_id = user_id_result.result[0][0]

        # Создаём клиента
        client_params = {
            'client_id': user_id,
            'title':     request.form.get('title', '').strip() or 'Клиент',
            'last_name': request.form.get('last_name', '').strip() or 'Не указано',
            'phone':     request.form.get('phone', '').strip() or 'Не указано',
            'address':   request.form.get('address', '').strip() or 'Не указано',
            'mkad':      1 if request.form.get('mkad') else 0
        }

        client_result = model_route(provider, client_params, 'register_client.sql')
        if not (client_result.status and client_result.result > 0):
            log.error("Не удалось создать запись клиента — откатить пользователя?")
            # Здесь можно добавить откат (удаление пользователя), но это опционально
            flash('Ошибка создания профиля клиента', 'danger')
            return redirect(url_for('blueprint_auth.register_client'))

        flash('Регистрация успешна! Теперь можно войти.', 'success')
        log.info(f"Клиент зарегистрирован: {username} (ID={user_id})")
        return redirect(url_for('blueprint_auth.login'))

    except Exception as e:
        log.exception(f"Ошибка регистрации клиента: {e}")
        flash('Произошла ошибка при регистрации', 'danger')
        return redirect(url_for('blueprint_auth.register_client'))


# ─── Admin-only staff/admin creation ───
@blueprint_auth.route('/register-staff', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def register_staff():
    if request.method == 'GET':
        log.info("Открыта форма создания сотрудника/админа (админ-панель)")
        return render_template('register_staff.html')

    try:
        username = request.form['username'].strip()
        lastname = request.form['lastname'].strip()
        email    = request.form['email'].strip()
        password = request.form['password']
        position     = request.form['position']
        role     = request.form['role']

        if role not in ('staff', 'admin'):
            flash('Можно создавать только сотрудников или администраторов', 'danger')
            return redirect(url_for('blueprint_auth.register_staff'))

        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

        user_params = {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'role': role
        }

        result_user = model_route(provider, user_params, 'register_user.sql')

        if not result_user.status or result_user.result == 0:
            flash('Логин или email уже заняты', 'danger')
            return redirect(url_for('blueprint_auth.register_staff'))

        user_id_result = model_route(provider, {'username': username}, 'get_user_id.sql')
        if not user_id_result.status or not user_id_result.result:
            flash('Внутренняя ошибка', 'danger')
            return redirect(url_for('blueprint_auth.register_staff'))

        user_id = user_id_result.result[0][0]

        # Создаём запись staff (для обеих ролей staff и admin)
        staff_params = {
            'staff_id':    user_id,
            'last_name':   request.form.get('lastname', '').strip() or 'Не указано',
            'address':     request.form.get('address', '').strip() or 'Не указано',
            'date_of_birth': request.form.get('date_of_birth') or None,
            'position':    request.form.get('position', 'driver'),
            'hire_date':   request.form.get('hire_date') or datetime.now().date().isoformat()
        }

        staff_result = model_route(provider, staff_params, 'register_staff.sql')
        if not (staff_result.status and staff_result.result > 0):
            flash('Ошибка создания профиля сотрудника', 'danger')
            return redirect(url_for('blueprint_auth.register_staff'))

        flash(f'{role.capitalize()} успешно создан!', 'success')
        log.info(f"{role.upper()} создан: {username} (ID={user_id})")
        return redirect(url_for('blueprint_auth.login'))   # или в список сотрудников

    except Exception as e:
        log.exception(f"Ошибка создания сотрудника/админа: {e}")
        flash('Произошла ошибка', 'danger')
        return redirect(url_for('blueprint_auth.register_staff'))