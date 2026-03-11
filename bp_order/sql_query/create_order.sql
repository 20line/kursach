INSERT INTO orders (
    transportation_date,
    client_id,
    total_weight,
    total_items
) VALUES (
    %(transportation_date)s,
    %(client_id)s,
    %(total_weight)s,
    %(total_items)s
);