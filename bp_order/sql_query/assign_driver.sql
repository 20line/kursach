UPDATE orders
SET staff_id=%(staff_id)s, state_id=2
WHERE order_id=%(order_id)s;