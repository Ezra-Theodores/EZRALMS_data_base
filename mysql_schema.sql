-- EZRA LMS Database Schema
-- Database: ezralms_db

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS ezralms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE ezralms_db;

-- Table: attendance
-- Menyimpan data kehadiran siswa dari Firestore
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    firestore_id VARCHAR(255) UNIQUE NOT NULL,
    student_id VARCHAR(255),
    student_name VARCHAR(255),
    class_id VARCHAR(255),
    class_name VARCHAR(255),
    date DATE,
    status ENUM('present', 'absent', 'late', 'excused', 'sick') DEFAULT 'present',
    check_in_time TIME,
    check_out_time TIME,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    raw_data JSON,
    INDEX idx_student_id (student_id),
    INDEX idx_class_id (class_id),
    INDEX idx_date (date),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: sync_log
-- Menyimpan log sinkronisasi
CREATE TABLE IF NOT EXISTS sync_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    collection_name VARCHAR(255),
    records_synced INT DEFAULT 0,
    sync_status ENUM('success', 'failed', 'partial') DEFAULT 'success',
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    INDEX idx_sync_status (sync_status),
    INDEX idx_started_at (started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: students (optional, if needed)
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    firestore_id VARCHAR(255) UNIQUE,
    student_code VARCHAR(50) UNIQUE,
    full_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    grade_level VARCHAR(50),
    class_group VARCHAR(50),
    enrollment_date DATE,
    status ENUM('active', 'inactive', 'graduated', 'transferred') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    raw_data JSON,
    INDEX idx_student_code (student_code),
    INDEX idx_status (status),
    INDEX idx_grade_level (grade_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- View: attendance_summary
CREATE OR REPLACE VIEW attendance_summary AS
SELECT
    class_id,
    class_name,
    date,
    COUNT(*) as total_students,
    SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present_count,
    SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent_count,
    SUM(CASE WHEN status = 'late' THEN 1 ELSE 0 END) as late_count,
    SUM(CASE WHEN status = 'sick' THEN 1 ELSE 0 END) as sick_count
FROM attendance
GROUP BY class_id, class_name, date;
