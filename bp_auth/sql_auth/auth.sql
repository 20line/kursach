SELECT 
    user_id,
    username,
    password_hash,
    role
FROM users 
WHERE username = %(username)s 
LIMIT 1;