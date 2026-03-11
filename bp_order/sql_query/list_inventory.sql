SELECT item_id, name, price_flat
FROM inventory_items
WHERE is_active = 1
ORDER BY name;
