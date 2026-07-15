
# Data Model Documentation: RecoverX

## 1. Overview
This document describes the data model for the RecoverX payment analytics platform, detailing the database entities, attributes, and relationships.

## 2. Entity-Relationship (ER) Model

### Core Entities
1. **transactions**: Core payment transaction records
2. **payment_retries**: Retry attempts for failed transactions
3. **bank_response_codes**: Bank response code lookup and classification
4. **failure_classifications**: Automated failure classification results
5. **alert_rules**: Alert configuration rules
6. **alerts**: Generated alert notifications

### Relationships
- **transactions** → **payment_retries**: 1-to-many (one transaction can have multiple retries)
- **transactions** → **failure_classifications**: 1-to-1 (one transaction has one classification)
- **bank_response_codes** → **payment_retries**: 1-to-many (one response code can be used in multiple retries)
- **alert_rules** → **alerts**: 1-to-many (one rule can generate multiple alerts)

## 3. Detailed Table Schemas

### Table: transactions
Stores core payment transaction information.
| Column Name       | Data Type         | Constraints          | Description                                  |
|-------------------|-------------------|----------------------|----------------------------------------------|
| transaction_id    | VARCHAR(100)      | PRIMARY KEY          | Unique transaction identifier                |
| customer_id       | VARCHAR(100)      | NOT NULL             | Customer identifier                          |
| amount            | DECIMAL(15,2)     | NOT NULL             | Transaction amount                           |
| currency          | VARCHAR(10)       | DEFAULT 'USD'        | Currency code                                |
| payment_method    | VARCHAR(100)      |                      | Payment method used                          |
| gateway           | VARCHAR(100)      |                      | Payment gateway used                         |
| initial_status    | VARCHAR(50)       | NOT NULL             | Initial transaction status                   |
| final_status      | VARCHAR(50)       |                      | Final transaction status                     |
| created_at        | TIMESTAMP         | NOT NULL             | Transaction creation time                    |
| updated_at        | TIMESTAMP         | AUTO UPDATE          | Last update time                             |

**Indexes**:
- idx_customer (customer_id)
- idx_created (created_at)
- idx_final_status (final_status)

---

### Table: payment_retries
Tracks all retry attempts for failed transactions.
| Column Name       | Data Type         | Constraints          | Description                                  |
|-------------------|-------------------|----------------------|----------------------------------------------|
| retry_id          | INT               | PRIMARY KEY, AUTO INCREMENT | Unique retry identifier               |
| transaction_id    | VARCHAR(100)      | FOREIGN KEY          | Associated transaction ID                    |
| attempt_number    | INT               | NOT NULL             | Retry attempt number (1, 2, 3...)           |
| retry_timestamp   | TIMESTAMP         | NOT NULL             | Time of retry attempt                        |
| retry_status      | VARCHAR(50)       | NOT NULL             | Status of this retry attempt                 |
| response_code     | VARCHAR(50)       |                      | Bank response code                           |
| response_message  | TEXT              |                      | Bank response message                        |

**Foreign Key**: transaction_id → transactions(transaction_id) (ON DELETE CASCADE)
**Indexes**:
- idx_transaction (transaction_id)
- idx_retry_time (retry_timestamp)

---

### Table: bank_response_codes
Lookup table for bank response codes and their classifications.
| Column Name       | Data Type         | Constraints          | Description                                  |
|-------------------|-------------------|----------------------|----------------------------------------------|
| response_code     | VARCHAR(50)       | PRIMARY KEY          | Bank response code                           |
| bank_name         | VARCHAR(100)      |                      | Name of issuing bank                         |
| description       | TEXT              | NOT NULL             | Description of the response code             |
| failure_type      | ENUM              | NOT NULL             | TEMPORARY or PERMANENT failure               |
| recovery_potential| DECIMAL(3,2)      |                      | Recovery potential score (0.00 to 1.00)      |
| recommended_action| TEXT              |                      | Recommended action for this code             |
| created_at        | TIMESTAMP         | DEFAULT NOW          | Record creation time                         |

---

### Table: failure_classifications
Stores automated failure classification results.
| Column Name       | Data Type         | Constraints          | Description                                  |
|-------------------|-------------------|----------------------|----------------------------------------------|
| classification_id | INT               | PRIMARY KEY, AUTO INCREMENT | Unique classification ID           |
| transaction_id    | VARCHAR(100)      | FOREIGN KEY          | Associated transaction ID                    |
| failure_type      | ENUM              | NOT NULL             | TEMPORARY or PERMANENT                       |
| root_cause        | TEXT              |                      | Identified root cause of failure             |
| recovery_score    | DECIMAL(3,2)      |                      | Recovery score (0.00 to 1.00)                |
| is_high_value     | BOOLEAN           | DEFAULT FALSE        | Flag for high-value transactions             |
| classified_at     | TIMESTAMP         | DEFAULT NOW          | Classification time                          |

**Foreign Key**: transaction_id → transactions(transaction_id) (ON DELETE CASCADE)
**Indexes**:
- idx_transaction (transaction_id)
- idx_failure_type (failure_type)
- idx_recovery_score (recovery_score)

---

### Table: alert_rules
Configuration rules for generating alerts.
| Column Name       | Data Type         | Constraints          | Description                                  |
|-------------------|-------------------|----------------------|----------------------------------------------|
| rule_id           | INT               | PRIMARY KEY, AUTO INCREMENT | Unique rule ID                      |
| rule_name         | VARCHAR(100)      | NOT NULL             | Name of the alert rule                       |
| rule_type         | VARCHAR(50)       | NOT NULL             | Type of rule (failure_rate, response_trend)  |
| threshold_value   | DECIMAL(15,2)     |                      | Threshold value for triggering               |
| threshold_condition | VARCHAR(20)     |                      | Condition (&gt;, &lt;, &gt;=, &lt;=, =)                  |
| is_active         | BOOLEAN           | DEFAULT TRUE         | Rule activation status                       |
| created_at        | TIMESTAMP         | DEFAULT NOW          | Rule creation time                           |
| updated_at        | TIMESTAMP         | AUTO UPDATE          | Last update time                             |

---

### Table: alerts
Stores generated alert notifications.
| Column Name       | Data Type         | Constraints          | Description                                  |
|-------------------|-------------------|----------------------|----------------------------------------------|
| alert_id          | INT               | PRIMARY KEY, AUTO INCREMENT | Unique alert ID                     |
| rule_id           | INT               | FOREIGN KEY          | Associated rule ID (optional)                |
| alert_type        | VARCHAR(50)       | NOT NULL             | Type of alert                                |
| message           | TEXT              | NOT NULL             | Alert message text                           |
| severity          | ENUM              | NOT NULL             | LOW, MEDIUM, HIGH, CRITICAL                  |
| is_resolved       | BOOLEAN           | DEFAULT FALSE        | Resolution status                            |
| created_at        | TIMESTAMP         | DEFAULT NOW          | Alert creation time                          |
| resolved_at       | TIMESTAMP         | NULLABLE             | Resolution time                              |

**Foreign Key**: rule_id → alert_rules(rule_id) (ON DELETE SET NULL)
**Indexes**:
- idx_severity (severity)
- idx_created (created_at)
- idx_resolved (is_resolved)

