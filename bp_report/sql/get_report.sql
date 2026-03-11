SELECT rep_id, total_quantity, total_revenue
FROM report
WHERE rep_month = %s AND rep_year = %s;