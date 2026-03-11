SELECT vehicle_id 
FROM vehicles 
WHERE capacity >= %(capacity)s 
    AND vehicle_state = 'available'
LIMIT 1