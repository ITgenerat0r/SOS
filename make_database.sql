CREATE DATABASE telegram_bot_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE telegram_bot_db;

CREATE TABLE user (
    id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    hashpass VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE banner (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message TEXT NOT NULL,
    author BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    send_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (author) REFERENCES user(id) ON DELETE CASCADE
);

CREATE TABLE bound (
    id INT AUTO_INCREMENT PRIMARY KEY,
    banner_id INT NOT NULL,
    receiver BIGINT NOT NULL,
    FOREIGN KEY (banner_id) REFERENCES banner(id) ON DELETE CASCADE
);