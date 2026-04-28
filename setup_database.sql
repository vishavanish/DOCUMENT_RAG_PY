-- Create database
CREATE DATABASE IF NOT EXISTS news_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create dedicated user with restricted permissions
CREATE USER IF NOT EXISTS 'news_user'@'localhost' IDENTIFIED BY 'news_password';

-- Grant necessary permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON news_db.* TO 'news_user'@'localhost';

-- Apply changes
FLUSH PRIVILEGES;

-- Use the database
USE news_db;