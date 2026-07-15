CREATE DATABASE IF NOT EXISTS recoverx;
USE recoverx;

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR(100) PRIMARY KEY,
    customer_id VARCHAR(100) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    payment_method VARCHAR(100),
    gateway VARCHAR(100),
    initial_status VARCHAR(50) NOT NULL,
    final_status VARCHAR(50),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_customer (customer_id),
    INDEX idx_created (created_at),
    INDEX idx_final_status (final_status)
);

CREATE TABLE IF NOT EXISTS payment_retries (
    retry_id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id VARCHAR(100) NOT NULL,
    attempt_number INT NOT NULL,
    retry_timestamp TIMESTAMP NOT NULL,
    retry_status VARCHAR(50) NOT NULL,
    response_code VARCHAR(50),
    response_message TEXT,
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    INDEX idx_transaction (transaction_id),
    INDEX idx_retry_time (retry_timestamp)
);

CREATE TABLE IF NOT EXISTS bank_response_codes (

    response_code VARCHAR(10) PRIMARY KEY,

    description VARCHAR(255) NOT NULL,

    failure_type ENUM('Temporary','Permanent') NOT NULL,

    recoverable BOOLEAN NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);

CREATE TABLE IF NOT EXISTS payment_classifications (

    classification_id INT AUTO_INCREMENT PRIMARY KEY,

    transaction_id VARCHAR(100) NOT NULL,

    response_code VARCHAR(10),

    failure_type ENUM('Temporary','Permanent'),

    recovery_score DECIMAL(5,2),

    final_status VARCHAR(50),

    classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (transaction_id)
        REFERENCES transactions(transaction_id)
        ON DELETE CASCADE,

    FOREIGN KEY (response_code)
        REFERENCES bank_response_codes(response_code)

);

INSERT INTO bank_response_codes
(response_code, description, failure_type, recoverable)
VALUES

('00', 'Approved', 'Temporary', TRUE),

('05', 'Do Not Honor', 'Permanent', FALSE),

('14', 'Invalid Card Number', 'Permanent', FALSE),

('51', 'Insufficient Funds', 'Temporary', TRUE),

('54', 'Expired Card', 'Permanent', FALSE),

('91', 'Issuer Unavailable', 'Temporary', TRUE),

('96', 'System Error', 'Temporary', TRUE);