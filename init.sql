-- ============================================================================
-- CTOP University Database Initialization Script
-- Purpose: Educational database with intentional vulnerabilities for CTF
-- Vulnerabilities: SQL Injection in Login, IDOR in Grades/Fees/Messages
-- ============================================================================

-- Create the CTOP University database
DROP DATABASE IF EXISTS ctop_university;
CREATE DATABASE ctop_university CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ctop_university;

-- ============================================================================
-- TABLE 1: users (Login credentials table)
-- Vulnerability: SQL Injection in login form (auth_production.py uses string concatenation)
-- ============================================================================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(20) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(64) NOT NULL,
    email VARCHAR(100),
    full_name VARCHAR(100),
    program VARCHAR(100),
    semester INT,
    cgpa DECIMAL(4,2),
    is_admin BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_student_id (student_id)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE 2: courses
-- Contains course information for the university
-- ============================================================================
CREATE TABLE courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_code VARCHAR(20) NOT NULL UNIQUE,
    course_name VARCHAR(200),
    credits INT,
    semester INT,
    professor VARCHAR(100),
    INDEX idx_course_code (course_code)
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE 3: enrollments
-- Links students to their enrolled courses
-- ============================================================================
CREATE TABLE enrollments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    course_id INT,
    enrollment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_student (student_id),
    INDEX idx_course (course_id),
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE 4: grades
-- Vulnerability: IDOR - Sequential IDs allow viewing other students' grades
-- ============================================================================
CREATE TABLE grades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    course_id INT,
    grade VARCHAR(5),
    marks INT,
    semester INT,
    INDEX idx_student (student_id),
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE 5: fees
-- Vulnerability: IDOR - Can view other students' fee records
-- ============================================================================
CREATE TABLE fees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    semester INT,
    tuition_fee DECIMAL(10,2),
    hostel_fee DECIMAL(10,2),
    other_fees DECIMAL(10,2),
    total_amount DECIMAL(10,2),
    due_date DATE,
    paid BOOLEAN DEFAULT FALSE,
    INDEX idx_student (student_id),
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE 6: secrets
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
-- TABLE 7: messages
-- Vulnerability: IDOR - Sequential IDs allow unauthorized access to messages
-- ============================================================================
CREATE TABLE messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT,
    recipient_id INT,
    subject VARCHAR(200),
    content TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    INDEX idx_sender (sender_id),
    INDEX idx_recipient (recipient_id),
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================================
-- TABLE 8: payments
-- Payment history for fee transactions
-- ============================================================================
CREATE TABLE payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    fee_id INT,
    amount DECIMAL(10,2),
    payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    payment_method VARCHAR(50),
    transaction_id VARCHAR(100),
    INDEX idx_student (student_id),
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (fee_id) REFERENCES fees(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================================
-- SEED DATA: Users (Login credentials)
-- Password hashes are SHA256 of simple passwords
-- ============================================================================

-- Admin: username='admin', password='admin123'
INSERT INTO users (student_id, username, password_hash, email, full_name, program, semester, cgpa, is_admin) VALUES 
('ADMIN001', 'admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 
 'admin@ctop.edu', 'System Administrator', 'Administration', 0, 10.00, TRUE);

-- Regular students: all with password='password123'
INSERT INTO users (student_id, username, password_hash, email, full_name, program, semester, cgpa, is_admin) VALUES 
('2024CSE001', 'alice.sharma', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 
 'alice.sharma@ctop.edu', 'Alice Sharma', 'B.Tech Computer Science', 6, 9.85, FALSE),
('2024CSE002', 'bob.patel', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 
 'bob.patel@ctop.edu', 'Bob Patel', 'B.Tech Computer Science', 6, 8.92, FALSE),
('2024ECE001', 'charlie.kumar', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 
 'charlie.kumar@ctop.edu', 'Charlie Kumar', 'B.Tech Electronics', 4, 9.10, FALSE),
('2024MEC001', 'diana.reddy', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 
 'diana.reddy@ctop.edu', 'Diana Reddy', 'B.Tech Mechanical', 4, 9.45, FALSE),
('2024CSE003', 'eve.nair', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 
 'eve.nair@ctop.edu', 'Eve Nair', 'B.Tech Computer Science', 2, 8.75, FALSE);

-- ============================================================================
-- SEED DATA: Courses
-- ============================================================================
INSERT INTO courses (course_code, course_name, credits, semester, professor) VALUES 
('CS101', 'Introduction to Programming', 4, 1, 'Dr. Rajesh Verma'),
('CS201', 'Data Structures', 4, 3, 'Dr. Priya Sharma'),
('CS301', 'Database Systems', 4, 5, 'Dr. Amit Kumar'),
('CS401', 'Web Security', 3, 7, 'Dr. Sneha Patel'),
('MATH101', 'Calculus I', 3, 1, 'Dr. Ramesh Gupta'),
('MATH201', 'Linear Algebra', 3, 3, 'Dr. Kavita Singh'),
('EC201', 'Digital Electronics', 4, 3, 'Dr. Suresh Reddy'),
('ME101', 'Engineering Mechanics', 4, 1, 'Dr. Vikram Nair'),
('CS302', 'Operating Systems', 4, 5, 'Dr. Anjali Desai'),
('CS202', 'Algorithms', 4, 4, 'Dr. Rohit Mehta'),
('CS402', 'Machine Learning', 3, 7, 'Dr. Deepak Shah'),
('PHY101', 'Physics I', 3, 1, 'Dr. Sunita Rao');

-- ============================================================================
-- SEED DATA: Enrollments
-- ============================================================================
INSERT INTO enrollments (student_id, course_id) VALUES 
(2, 2), (2, 3), (2, 9), (2, 10),  -- Alice's courses
(3, 2), (3, 3), (3, 9),            -- Bob's courses
(4, 7), (4, 6), (4, 5),            -- Charlie's courses
(5, 8), (5, 12), (5, 5),           -- Diana's courses
(6, 1), (6, 5), (6, 12);           -- Eve's courses

-- ============================================================================
-- SEED DATA: Grades (IDOR target)
-- ============================================================================
INSERT INTO grades (student_id, course_id, grade, marks, semester) VALUES 
(2, 2, 'A+', 98, 5),
(2, 3, 'A', 95, 5),
(2, 9, 'A+', 99, 5),
(3, 2, 'B+', 82, 5),
(3, 3, 'A-', 88, 5),
(4, 7, 'A', 91, 3),
(4, 6, 'A+', 96, 3),
(5, 8, 'A', 94, 3),
(5, 12, 'A+', 97, 3),
(6, 1, 'B', 80, 1),
(6, 5, 'B+', 85, 1);

-- ============================================================================
-- SEED DATA: Fees (IDOR target)
-- ============================================================================
INSERT INTO fees (student_id, semester, tuition_fee, hostel_fee, other_fees, total_amount, due_date, paid) VALUES 
(2, 6, 75000.00, 15000.00, 5000.00, 95000.00, '2024-08-15', TRUE),
(3, 6, 75000.00, 15000.00, 5000.00, 95000.00, '2024-08-15', FALSE),
(4, 4, 70000.00, 15000.00, 5000.00, 90000.00, '2024-08-15', TRUE),
(5, 4, 70000.00, 0.00, 5000.00, 75000.00, '2024-08-15', TRUE),
(6, 2, 75000.00, 15000.00, 5000.00, 95000.00, '2024-08-15', FALSE);

-- ============================================================================
-- SEED DATA: Secrets (CTF FLAGS)
-- ============================================================================
INSERT INTO secrets (secret_name, secret_value, access_level) VALUES 
('sql_injection_flag', 'FLAG{SQL_INJECTION_IN_LOGIN_FORM}', 1),
('idor_grades_flag', 'FLAG{UNAUTHORIZED_GRADE_ACCESS}', 1),
('idor_fees_flag', 'FLAG{FINANCIAL_DATA_EXPOSED}', 1),
('admin_panel_flag', 'FLAG{ADMIN_PANEL_COMPROMISED}', 5),
('database_master_key', 'FLAG{DATABASE_SECRETS_EXTRACTED}', 10);

-- ============================================================================
-- SEED DATA: Messages (IDOR target)
-- ============================================================================
INSERT INTO messages (sender_id, recipient_id, subject, content, is_read) VALUES 
(1, 2, 'Welcome to CTOP University', 
 'Dear Alice, welcome to CTOP! Your admin verification code is: ADMIN-VERIFY-2024. Database credentials: ctop_user / ctop_secure_2024', FALSE),
(2, 3, 'Study Group for CS301', 
 'Hey Bob, want to form a study group for Database Systems? Let me know!', FALSE),
(1, 4, 'Scholarship Notification', 
 'Charlie, congratulations! You have been selected for the Merit Scholarship. Amount: ₹50,000', FALSE),
(1, 5, 'Hostel Allotment', 
 'Diana, your hostel has been allotted. Block: A, Room: 305. Access code: H-2024-A305', FALSE),
(1, 6, 'Fee Payment Reminder', 
 'Eve, your semester fees are overdue. Please clear dues immediately to avoid academic hold.', FALSE),
(3, 2, 'Re: Study Group', 
 'Sure Alice! Let\'s meet at the library tomorrow at 4 PM.', TRUE),
(1, 2, 'Grade Update - CS301', 
 'Alice, your CS301 assignment grades have been updated. Please check the portal.', FALSE);

-- ============================================================================
-- SEED DATA: Payments
-- ============================================================================
INSERT INTO payments (student_id, fee_id, amount, payment_method, transaction_id) VALUES 
(2, 1, 95000.00, 'UPI', 'TXN2024080112345'),
(4, 3, 90000.00, 'Net Banking', 'TXN2024080198765'),
(5, 4, 75000.00, 'Credit Card', 'TXN2024080154321');

-- ============================================================================
-- CREATE APPLICATION USER
-- Grant necessary privileges to the CTOP application
-- ============================================================================
CREATE USER IF NOT EXISTS 'ctop_user'@'%' IDENTIFIED BY 'ctop_secure_2024';
GRANT SELECT, INSERT, UPDATE, DELETE ON ctop_university.* TO 'ctop_user'@'%';
FLUSH PRIVILEGES;

-- ============================================================================
-- Initialization Complete
-- ============================================================================
SELECT 'CTOP University Database initialized successfully!' AS Status;
SELECT 'Login credentials: admin/admin123, alice.sharma/password123, etc.' AS Info;
SELECT 'Database contains 8 tables: students, courses, enrollments, grades, fees, messages, payments, secrets' AS Schema;
