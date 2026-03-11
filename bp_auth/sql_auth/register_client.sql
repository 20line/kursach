INSERT INTO clients (
    client_id, title, last_name, phone, address, MKAD
) VALUES (
    %(client_id)s, %(title)s, %(last_name)s, %(phone)s, %(address)s, %(mkad)s
);