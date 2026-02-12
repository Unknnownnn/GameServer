-- ============================================================================
-- CTF Database Initialization Script
-- Purpose: Educational database with intentional vulnerabilities
-- Vulnerabilities: SQL Injection, IDOR, Truncation Attacks, Race Conditions
-- ============================================================================

-- Create the CTF database
DROP DATABASE IF EXISTS ctf_db;
CREATE DATABASE ctf_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ctf_db;

-- ============================================================================
-- TABLE 1: users
-- Vulnerability: SQL Truncation & Second-Order SQL Injection
-- The 20-char username limit enables 'admin' + spaces + 'x' registration attacks
-- ============================================================================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(20) NOT NULL UNIQUE,
    password_hash VARCHAR(64) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    bio TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE 2: secrets
-- Vulnerability: SQL Injection target - contains valuable flags
-- ============================================================================
CREATE TABLE secrets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    secret_name VARCHAR(50),
    secret_value VARCHAR(100),
    access_level INT DEFAULT 10,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE 3: messages
-- Vulnerability: IDOR - Sequential IDs allow unauthorized access
-- ============================================================================
CREATE TABLE messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT,
    recipient_id INT,
    content TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    INDEX idx_sender (sender_id),
    INDEX idx_recipient (recipient_id)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE 4: coupons
-- Vulnerability: Race Conditions - concurrent redemption vulnerability
-- ============================================================================
CREATE TABLE coupons (
    code VARCHAR(20) PRIMARY KEY,
    discount_percent INT,
    max_uses INT,
    current_uses INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================================
-- SEED DATA: Users
-- Password hashes are SHA256 of simple passwords for testing
-- ============================================================================

-- Admin user: username='admin', password='admin123'
-- SHA256('admin123') = 240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9
INSERT INTO users (username, password_hash, is_admin, bio) VALUES 
('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', TRUE, 
 'System administrator with full access to all resources.');

-- Demo user: username='demo_user', password='demo123'
-- SHA256('demo123') = aec070645fe53ee3b3763059376134f058cc337247c978add178b6ccdfb0019f
INSERT INTO users (username, password_hash, is_admin, bio) VALUES 
('demo_user', 'aec070645fe53ee3b3763059376134f058cc337247c978add178b6ccdfb0019f', FALSE, 
 'Standard demo user account for testing.');

-- Additional test users: all with password='password123'
-- SHA256('password123') = ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f
INSERT INTO users (username, password_hash, is_admin, bio) VALUES 
('alice', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', FALSE, 
 'Alice loves cryptography and secure systems.'),
('bob', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', FALSE, 
 'Bob is learning web security fundamentals.'),
('charlie', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', FALSE, 
 'Charlie enjoys finding vulnerabilities ethically.'),
('eve', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', FALSE, 
 'Eve is interested in penetration testing.');

-- ============================================================================
-- SEED DATA: Secrets (FLAGS)
-- ============================================================================
INSERT INTO secrets (secret_name, secret_value, access_level) VALUES 
('sql_injection_flag', 'FLAG{SQL_INJECTION_MASTER}', 1),
('admin_credentials_flag', 'FLAG{HIDDEN_ADMIN_CREDENTIALS}', 1),
('super_secret_key', 'FLAG{Y0U_F0UND_TH3_K3Y}', 5),
('database_backup_password', 'backup_p@ssw0rd_2024', 10),
('api_master_token', 'sk_live_51AbCdEfGhIjKlMnOpQrStUv', 10);

-- ============================================================================
-- SEED DATA: Messages (for IDOR testing)
-- ============================================================================
INSERT INTO messages (sender_id, recipient_id, content, is_read) VALUES 
(1, 2, 'Welcome to the CTF platform, demo_user! Your admin verification code is: ADM1N-V3R1FY-2024', FALSE),
(2, 1, 'Thank you! I am excited to participate in this challenge.', TRUE),
(3, 4, 'Hey Bob, did you solve the SQL injection challenge yet?', FALSE),
(4, 3, 'Not yet Alice, I am still working on bypassing the login form.', FALSE),
(5, 6, 'Charlie, I found a potential IDOR vulnerability in the messages endpoint.', FALSE),
(6, 5, 'Good find Eve! Let me know if you can extract any sensitive data.', FALSE),
(1, 3, 'Alice, your account has been flagged for suspicious activity. Please review.', FALSE),
(1, 5, 'Charlie, congratulations on completing Level 1! Here is your reward code: RWD-L1-8X9K', FALSE);

-- ============================================================================
-- SEED DATA: Coupons (for race condition testing)
-- ============================================================================
INSERT INTO coupons (code, discount_percent, max_uses, current_uses) VALUES 
('SUMMER2024', 50, 1, 0),
('WELCOME10', 10, 100, 45),
('VIPONLY', 75, 5, 2),
('LIMITEDEDITION', 90, 1, 0),
('FREESHIP', 100, 10, 7);

-- ============================================================================
-- CREATE APPLICATION USER
-- Grant necessary privileges to the CTF player account
-- ============================================================================
CREATE USER IF NOT EXISTS 'ctf_player'@'%' IDENTIFIED BY 'player_password_456';
GRANT SELECT, INSERT, UPDATE, DELETE ON ctf_db.* TO 'ctf_player'@'%';
FLUSH PRIVILEGES;

-- ============================================================================
-- Initialization Complete
-- ============================================================================
SELECT 'CTF Database initialized successfully!' AS Status;
