INSERT INTO staff (
    staff_id, last_name, address, date_of_birth, position, hire_date
) VALUES (
    %(staff_id)s, %(last_name)s, %(address)s, %(date_of_birth)s, %(position)s, %(hire_date)s
);