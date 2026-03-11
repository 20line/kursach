SELECT staff_id, last_name, fee_flat
FROM staff
WHERE staff_type = 'producer'
  AND staff_state = 'available'
ORDER BY last_name;
