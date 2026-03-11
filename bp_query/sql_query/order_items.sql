SELECT
  ii.item_id,
  ii.name,
  ii.price_flat
FROM booking_inventory bi
JOIN inventory_items ii ON ii.item_id = bi.item_id
WHERE bi.booking_id = %(booking_id)s
ORDER BY ii.name;