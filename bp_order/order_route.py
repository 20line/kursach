import os
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from access import login_required, role_required
from model_route import model_route
from database.sql_provider import SQLProvider
from datetime import datetime
from database.tx import transaction

import logging
log = logging.getLogger(__name__)

blueprint_order = Blueprint(
    'blueprint_order',
    __name__,
    template_folder='templates'
)

# Инициализация провайдера SQL
provider = SQLProvider(os.path.join(os.path.dirname(__file__), 'sql_query'))

ROOM_FEE_FLAT = 1000.00


@blueprint_order.route('/', methods=['GET'])
@login_required
@role_required('client')
def show_products():
    inventory_info = model_route(provider, {}, 'list_inventory.sql')
    producers_info = model_route(provider, {}, 'list_available_producers.sql')

    inventory_items = []
    if inventory_info.status and inventory_info.result:
        inventory_items = [
            {'item_id': row[0], 'name': row[1], 'price_flat': float(row[2])}
            for row in inventory_info.result
        ]

    producers = []
    if producers_info.status and producers_info.result:
        producers = [
            {'staff_id': row[0], 'last_name': row[1], 'fee_flat': float(row[2])}
            for row in producers_info.result
        ]

    return render_template(
        'create_order.html',
        room_fee_flat=float(ROOM_FEE_FLAT),
        inventory_items=inventory_items,
        producers=producers,
    )


@blueprint_order.route('/create_booking', methods=['POST'])
@login_required
@role_required('client')
def create_booking():
    log.info(
        "Создание бронирования | Пользователь: %s | user_id: %s",
        session.get('username'),
        session.get('user_id'),
    )

    client_id = session.get('client_id')
    if not client_id:
        flash('Вы не являетесь клиентом', 'danger')
        return redirect(url_for('blueprint_order.show_products'))

    start_at_raw = request.form.get('start_at', '').strip()
    end_at_raw = request.form.get('end_at', '').strip()

    try:
        start_at = datetime.fromisoformat(start_at_raw)
        end_at = datetime.fromisoformat(end_at_raw)
    except ValueError:
        flash('Некорректный формат даты/времени', 'danger')
        return redirect(url_for('blueprint_order.show_products'))

    if start_at >= end_at:
        flash('Время начала должно быть меньше времени окончания', 'danger')
        return redirect(url_for('blueprint_order.show_products'))

    producer_id_raw = (request.form.get('producer_id') or '').strip()
    producer_id = int(producer_id_raw) if producer_id_raw.isdigit() else None

    raw_item_ids = request.form.getlist('inventory_item')
    item_ids = []
    for x in raw_item_ids:
        x = (x or '').strip()
        if x.isdigit():
            item_ids.append(int(x))
    item_ids = sorted(set(item_ids))

    start_at_db = start_at.strftime('%Y-%m-%d %H:%M:%S')
    end_at_db = end_at.strftime('%Y-%m-%d %H:%M:%S')

    try:
        with transaction() as cur:
            # Single active room
            cur.execute(
                "SELECT room_id FROM rooms WHERE is_active = 1 LIMIT 1 FOR UPDATE"
            )
            room_row = cur.fetchone()
            if not room_row:
                raise ValueError("Нет активной комнаты для бронирования")
            room_id = room_row[0]

            print("1")

            # Booking state: confirmed (option B)
            cur.execute(
                "SELECT state_id FROM booking_state WHERE name = 'confirmed' LIMIT 1"
            )
            state_row = cur.fetchone()
            if not state_row:
                raise RuntimeError("Не найдено состояние booking_state='confirmed'")
            confirmed_state_id = state_row[0]

            print("2")

            # Overlap check for active bookings (pending/confirmed)
            cur.execute(
                """
                SELECT b.booking_id
                FROM bookings b
                WHERE b.room_id = %s
                  AND b.state_id IN (
                    SELECT state_id FROM booking_state WHERE name IN ('pending', 'confirmed')
                  )
                  AND b.start_at < %s
                  AND b.end_at > %s
                LIMIT 1
                FOR UPDATE
                """,
                (room_id, end_at_db, start_at_db),
            )
            if cur.fetchone():
                raise ValueError("Это время уже занято. Выберите другое время.")

            print("3")

            # Inventory total
            inventory_total = 0.0
            if item_ids:
                placeholders = ",".join(["%s"] * len(item_ids))
                cur.execute(
                    f"""
                    SELECT IFNULL(SUM(price_flat), 0)
                    FROM inventory_items
                    WHERE is_active = 1 AND item_id IN ({placeholders})
                    """,
                    tuple(item_ids),
                )
                inventory_total = float(cur.fetchone()[0] or 0)

            print("4")
            
            # Producer check + fee
            producer_fee = 0.0
            if producer_id is not None:
                cur.execute(
                    """
                    SELECT staff_id, staff_state, fee_flat
                    FROM staff
                    WHERE staff_id = %s AND staff_type = 'producer'
                    FOR UPDATE
                    """,
                    (producer_id,),
                )
                prow = cur.fetchone()
                if not prow:
                    raise ValueError("Выбранный продюсер не найден")
                if prow[1] != 'available':
                    raise ValueError("Выбранный продюсер сейчас недоступен")
                producer_fee = float(prow[2] or 0)

            total_price = float(ROOM_FEE_FLAT) + inventory_total + producer_fee

            print("5")

            # Create booking
            cur.execute(
                """
                INSERT INTO bookings
                  (room_id, client_id, producer_id, start_at, end_at, total_price, state_id)
                VALUES
                  (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    room_id,
                    client_id,
                    producer_id,
                    start_at_db,
                    end_at_db,
                    total_price,
                    confirmed_state_id,
                ),
            )
            booking_id = cur.lastrowid
            if not booking_id:
                raise RuntimeError("Не удалось получить ID созданного бронирования")

            print("6")

            # Attach inventory
            for item_id in item_ids:
                cur.execute(
                    "INSERT INTO booking_inventory (booking_id, item_id) VALUES (%s, %s)",
                    (booking_id, item_id),
                )

            print("7")

            # Mark producer assigned if chosen
            if producer_id is not None:
                cur.execute(
                    "UPDATE staff SET staff_state = 'assigned' WHERE staff_id = %s",
                    (producer_id,),
                )
            
            print("8")


        flash(f'Бронирование №{booking_id} успешно создано!', 'success')
        return render_template('success.html', booking_id=booking_id)

    except ValueError as ve:
        flash(str(ve), 'warning')
    except Exception:
        log.exception("Критическая ошибка при создании бронирования")
        flash('Произошла ошибка при создании бронирования. Попробуйте позже.', 'danger')

    return redirect(url_for('blueprint_order.show_products'))


@blueprint_order.route('/assign_driver/<int:order_id>', methods=['POST'])
@login_required
@role_required('admin')
def assign_driver(order_id):
    flash("Функция назначения водителя отключена (проект переведён на бронирования студии).", "warning")
    return redirect(url_for('index'))

@blueprint_order.route('/finish_order/<int:order_id>', methods=['POST'])
@login_required
@role_required('admin')
def finish_order(order_id):
    flash("Функция завершения заказа отключена (проект переведён на бронирования студии).", "warning")
    return redirect(url_for('index'))