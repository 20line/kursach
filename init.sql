DROP DATABASE IF EXISTS studio_db;
CREATE DATABASE studio_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE studio_db;

-- 1. Users (auth)
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('client', 'staff', 'admin') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Clients (1-1 with users, keeps fields used by registration SQL)
CREATE TABLE clients (
    client_id INT PRIMARY KEY,
    title VARCHAR(255),
    last_name VARCHAR(255),
    phone VARCHAR(255),
    address VARCHAR(255),
    MKAD TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_clients_user
        FOREIGN KEY (client_id) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 3. Staff (1-1 with users, extended for studio logic)
CREATE TABLE staff (
    staff_id INT PRIMARY KEY,
    last_name VARCHAR(255),
    address VARCHAR(255),
    date_of_birth DATE NULL,
    position VARCHAR(255),
    hire_date DATE DEFAULT (CURRENT_DATE),
    staff_state ENUM('available', 'assigned') DEFAULT 'available',
    staff_type ENUM('producer', 'staff', 'admin_staff') DEFAULT 'staff',
    fee_flat DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_staff_user
        FOREIGN KEY (staff_id) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 4. Rooms (single room studio, but extensible)
CREATE TABLE rooms (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    is_active TINYINT(1) DEFAULT 1
) ENGINE=InnoDB;

-- 5. Inventory items (checkbox add-ons, flat price per booking)
CREATE TABLE inventory_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    price_flat DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    is_active TINYINT(1) DEFAULT 1
) ENGINE=InnoDB;

-- 6. Booking state
CREATE TABLE booking_state (
    state_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
) ENGINE=InnoDB;

INSERT INTO booking_state (name) VALUES
  ('pending'),
  ('confirmed'),
  ('finished'),
  ('cancelled');

-- 7. Bookings (core domain: single room, optional producer)
CREATE TABLE bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    client_id INT NOT NULL,
    producer_id INT NULL,
    start_at DATETIME NOT NULL,
    end_at DATETIME NOT NULL,
    total_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    state_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_bookings_room
        FOREIGN KEY (room_id) REFERENCES rooms(room_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_bookings_client
        FOREIGN KEY (client_id) REFERENCES clients(client_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_bookings_producer
        FOREIGN KEY (producer_id) REFERENCES staff(staff_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_bookings_state
        FOREIGN KEY (state_id) REFERENCES booking_state(state_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 8. Booking inventory (many-to-many: booking ↔ inventory_items)
CREATE TABLE booking_inventory (
    booking_id INT NOT NULL,
    item_id INT NOT NULL,
    PRIMARY KEY (booking_id, item_id),
    CONSTRAINT fk_booking_inventory_booking
        FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_booking_inventory_item
        FOREIGN KEY (item_id) REFERENCES inventory_items(item_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 9. Reporting tables for bookings

-- 9.1 Monthly summary by bookings and revenue
CREATE TABLE report_bookings_monthly_summary (
    report_id INT AUTO_INCREMENT PRIMARY KEY,
    report_month TINYINT UNSIGNED NOT NULL,
    report_year SMALLINT UNSIGNED NOT NULL,
    bookings_cnt INT UNSIGNED NOT NULL,
    total_revenue DECIMAL(12,2) NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_report_bookings_month (report_year, report_month)
) ENGINE=InnoDB;

-- 9.2 Top clients by revenue per month
CREATE TABLE report_top_clients_by_revenue (
    report_id INT AUTO_INCREMENT PRIMARY KEY,
    report_month TINYINT UNSIGNED NOT NULL,
    report_year SMALLINT UNSIGNED NOT NULL,
    client_id INT NOT NULL,
    client_last_name VARCHAR(255),
    bookings_cnt INT UNSIGNED NOT NULL,
    total_revenue DECIMAL(12,2) NOT NULL,
    rank_num INT UNSIGNED NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_report_top_clients (report_year, report_month, rank_num),
    KEY idx_report_top_clients_client (client_id),
    CONSTRAINT fk_report_top_clients_client
        FOREIGN KEY (client_id) REFERENCES clients(client_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 9.3 Largest bookings by price per month
CREATE TABLE report_largest_bookings_by_price (
    report_id INT AUTO_INCREMENT PRIMARY KEY,
    report_month TINYINT UNSIGNED NOT NULL,
    report_year SMALLINT UNSIGNED NOT NULL,
    booking_id INT NOT NULL,
    client_id INT NOT NULL,
    total_price DECIMAL(12,2) NOT NULL,
    rank_num INT UNSIGNED NOT NULL,
    start_at DATETIME,
    end_at DATETIME,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_report_largest_bookings (report_year, report_month, rank_num),
    KEY idx_report_largest_bookings_booking (booking_id),
    KEY idx_report_largest_bookings_client (client_id),
    CONSTRAINT fk_report_largest_bookings_booking
        FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_report_largest_bookings_client
        FOREIGN KEY (client_id) REFERENCES clients(client_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- 10. Seed basic data

-- 10.1 One studio room
INSERT INTO rooms (name, is_active) VALUES ('Main Studio Room', 1);

-- 10.2 Some inventory items (flat per booking)
INSERT INTO inventory_items (name, price_flat, is_active) VALUES
  ('Electric Guitar', 500.00, 1),
  ('Bass Guitar',    400.00, 1),
  ('Drum Kit',       700.00, 1),
  ('Keyboard',       450.00, 1),
  ('Vocal Mic',      200.00, 1);

-- 10.3 Example users (optional: mainly for having some rows in DB)
-- Password hashes here are placeholders; real users should be created via the web UI.

-- Admin user
INSERT INTO users (username, email, password_hash, role)
VALUES ('admin', 'admin@example.com', '$2b$12$lVMzW7TGb/M.cNKjsLe7wOt.3yeY2UR8.HZDFMNGntxfWT8EGvs.K', 'admin');

SET @admin_id = LAST_INSERT_ID();
INSERT INTO staff (staff_id, last_name, address, date_of_birth, position, hire_date,
                   staff_state, staff_type, fee_flat)
VALUES (@admin_id, 'Admin', 'N/A', NULL, 'administrator', CURRENT_DATE,
        'available', 'admin_staff', 0.00);

-- Example producer
INSERT INTO users (username, email, password_hash, role)
VALUES ('producer1', 'producer1@example.com', '$2b$12$lVMzW7TGb/M.cNKjsLe7wOt.3yeY2UR8.HZDFMNGntxfWT8EGvs.K', 'staff');

SET @producer_user_id = LAST_INSERT_ID();
INSERT INTO staff (staff_id, last_name, address, date_of_birth, position, hire_date,
                   staff_state, staff_type, fee_flat)
VALUES (@producer_user_id, 'Producer', 'Studio Address', NULL, 'producer', CURRENT_DATE,
        'available', 'producer', 1500.00);

-- Example client
INSERT INTO users (username, email, password_hash, role)
VALUES ('client1', 'client1@example.com', '$2b$12$lVMzW7TGb/M.cNKjsLe7wOt.3yeY2UR8.HZDFMNGntxfWT8EGvs.K', 'client');

SET @client_user_id = LAST_INSERT_ID();
INSERT INTO clients (client_id, title, last_name, phone, address, MKAD)
VALUES (@client_user_id, 'Клиент', 'Иванов', '+79990000000', 'Город', 1);

-- 11. Stored procedures for reports
DELIMITER //

-- 11.1 Monthly bookings summary
CREATE PROCEDURE generate_monthly_bookings_summary (
    IN p_month TINYINT,
    IN p_year SMALLINT
)
BEGIN
    DELETE FROM report_bookings_monthly_summary
    WHERE report_year = p_year AND report_month = p_month;

    INSERT INTO report_bookings_monthly_summary (
        report_month,
        report_year,
        bookings_cnt,
        total_revenue
    )
    SELECT
        p_month AS report_month,
        p_year  AS report_year,
        COUNT(b.booking_id) AS bookings_cnt,
        IFNULL(SUM(b.total_price), 0) AS total_revenue
    FROM bookings b
    WHERE
        MONTH(b.start_at) = p_month
        AND YEAR(b.start_at) = p_year;
END//

-- 11.2 Top clients by revenue in month (top-5)
CREATE PROCEDURE generate_top_clients_by_revenue (
    IN p_month TINYINT,
    IN p_year SMALLINT
)
BEGIN
    DECLARE v_limit INT DEFAULT 5;

    DELETE FROM report_top_clients_by_revenue
    WHERE report_year = p_year AND report_month = p_month;

    SET @r := 0;

    INSERT INTO report_top_clients_by_revenue (
        report_month,
        report_year,
        client_id,
        client_last_name,
        bookings_cnt,
        total_revenue,
        rank_num
    )
    SELECT
        p_month AS report_month,
        p_year  AS report_year,
        c.client_id,
        c.last_name,
        COUNT(b.booking_id) AS bookings_cnt,
        IFNULL(SUM(b.total_price), 0) AS total_revenue,
        (@r := @r + 1) AS rank_num
    FROM bookings b
    JOIN clients c ON c.client_id = b.client_id
    WHERE
        MONTH(b.start_at) = p_month
        AND YEAR(b.start_at) = p_year
    GROUP BY
        c.client_id, c.last_name
    ORDER BY
        total_revenue DESC
    LIMIT v_limit;
END//

-- 11.3 Largest bookings by price in month (top-5)
CREATE PROCEDURE generate_largest_bookings_by_price (
    IN p_month TINYINT,
    IN p_year SMALLINT
)
BEGIN
    DECLARE v_limit INT DEFAULT 5;

    DELETE FROM report_largest_bookings_by_price
    WHERE report_year = p_year AND report_month = p_month;

    SET @r2 := 0;

    INSERT INTO report_largest_bookings_by_price (
        report_month,
        report_year,
        booking_id,
        client_id,
        total_price,
        rank_num,
        start_at,
        end_at
    )
    SELECT
        p_month AS report_month,
        p_year  AS report_year,
        b.booking_id,
        b.client_id,
        b.total_price,
        (@r2 := @r2 + 1) AS rank_num,
        b.start_at,
        b.end_at
    FROM bookings b
    WHERE
        MONTH(b.start_at) = p_month
        AND YEAR(b.start_at) = p_year
    ORDER BY
        b.total_price DESC
    LIMIT v_limit;
END//

DELIMITER ;