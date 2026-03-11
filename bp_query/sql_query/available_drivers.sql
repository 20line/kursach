SELECT s.staff_id, s.last_name
FROM staff s
WHERE s.staff_type = 'producer'
  AND s.staff_state = 'available'
ORDER BY s.last_name;