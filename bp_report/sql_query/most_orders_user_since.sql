SELECT
    u.user_id          AS user_id,
    u.username         AS username,
    COUNT(b.booking_id)  AS booking_count,
    IFNULL(SUM(b.total_price), 0) AS total_revenue
FROM
    users u
INNER JOIN bookings b ON b.client_id = u.user_id
WHERE
    u.role = 'client'
    AND b.start_at >= %(since)s
GROUP BY
    u.user_id, u.username
ORDER BY
    booking_count DESC
LIMIT 1;