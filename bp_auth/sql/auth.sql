SELECT login, password, role_name
FROM employee
JOIN role ON employee.role_id = role.role_id
WHERE login = %s;
