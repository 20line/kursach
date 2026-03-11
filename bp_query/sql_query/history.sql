SELECT
  b.booking_id,
  b.start_at,
  b.end_at,
  b.total_price,
  bs.name AS booking_state
FROM bookings AS b
JOIN booking_state AS bs ON b.state_id = bs.state_id
WHERE b.client_id = %(client_id)s
ORDER BY b.start_at DESC;