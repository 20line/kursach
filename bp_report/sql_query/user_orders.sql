SELECT
    booking_id,
    start_at,
    end_at,
    total_price
FROM bookings
WHERE client_id = %(client_id)s
ORDER BY start_at DESC;