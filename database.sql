CREATE DATABASE IF NOT EXISTS pengaduan_masyarakat CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE pengaduan_masyarakat;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(190) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('citizen', 'admin') NOT NULL DEFAULT 'citizen',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(180) NOT NULL,
    category ENUM('Infrastruktur', 'Lingkungan', 'Pelayanan Publik', 'Keamanan', 'Sosial', 'Aspirasi', 'Lainnya') NOT NULL,
    location VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    evidence VARCHAR(255) NULL,
    status ENUM('Menunggu', 'Diproses', 'Selesai', 'Ditolak') NOT NULL DEFAULT 'Menunggu',
    admin_response TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_reports_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_reports_user_created (user_id, created_at),
    INDEX idx_reports_status (status)
);
USE pengaduan_masyarakat;

DESCRIBE users;
DESCRIBE reports;
USE pengaduan_masyarakat;
DESCRIBE users;
USE pengaduan_masyarakat;

UPDATE users
SET role = 'admin'
WHERE email = 'hatmanfirdayat@gmail.com';

SELECT id, nama, email, role
FROM users;
