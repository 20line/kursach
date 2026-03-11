SELECT
  b.booking_id,
  b.start_at,
  b.end_at,
  b.total_price,
  bs.name AS booking_state
FROM bookings AS b
JOIN booking_state AS bs ON b.state_id = bs.state_id
JOIN users u ON b.client_id = u.user_id
WHERE u.username = %(username)s
ORDER BY b.start_at DESC;