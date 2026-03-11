INSERT INTO order_items (
    order_id,
    name,
    weight,
    amount
) VALUES (
    %(order_id)s,
    %(name)s,
    %(weight)s,
    %(amount)s
)