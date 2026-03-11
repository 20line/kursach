SELECT
  b.booking_id,
  b.start_at,
  b.end_at,
  b.room_id,
  b.client_id,
  b.producer_id,
  b.total_price,
  bs.name AS booking_state
FROM bookings AS b
JOIN booking_state AS bs ON b.state_id = bs.state_id
WHERE b.booking_id = %(booking_id)s;