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
    bank_name VARCHAR(100),
    description VARCHAR(255) NOT NULL,
    failure_type ENUM('TEMPORARY','PERMANENT') NOT NULL,
    recovery_potential DECIMAL(5,2),
    recommended_action TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS failure_classifications (
    classification_id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id VARCHAR(100) NOT NULL,
    failure_type ENUM('TEMPORARY','PERMANENT'),
    root_cause TEXT,
    recovery_score DECIMAL(5,2),
    is_high_value BOOLEAN,
    classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id)
        REFERENCES transactions(transaction_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS alert_rules (
    rule_id INT AUTO_INCREMENT PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    threshold_value DECIMAL(10,2) NOT NULL,
    threshold_condition VARCHAR(10) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    rule_id INT,
    alert_type VARCHAR(50) NOT NULL,
    message TEXT,
    severity VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rule_id) REFERENCES alert_rules(rule_id) ON DELETE SET NULL
);