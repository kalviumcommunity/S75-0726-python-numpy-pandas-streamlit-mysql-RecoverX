
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

---

## 4. Derived Metrics / Virtual Attributes

These are not stored columns but are computed at query time and drive analytics + UI reports.

### 4.1 Priority Score (Retry Prioritization)
Computed in `src/payment_queries.py` by `get_prioritized_transactions_to_retry()` and returned as column `priority_score`.

Formula:
```
priority_score =
    COALESCE(failure_classifications.recovery_score, bank_response_codes.recovery_potential, 0) * 100
  + (CASE WHEN failure_classifications.is_high_value THEN 10 ELSE 0 END)
  + LEAST(transactions.amount / 100, 10)
  - COALESCE(retry_attempts_count, 0) * 5
```

Candidate filter:
- `transactions.final_status IS NULL OR transactions.final_status != 'SUCCESS'`
- `retry_attempts_count < max_attempts` (default `3`)

Columns returned (DataFrame):
`transaction_id, customer_id, amount, currency, payment_method, gateway, initial_status, final_status, created_at, retry_attempts, last_retry_at, last_retry_status, last_response_code, failure_type, recovery_score, recommended_action, failure_description, priority_score`.

Order: `priority_score DESC, created_at DESC`, `LIMIT limit` (default `50`).

### 4.2 Revenue Recovery Summary
Computed in `get_revenue_recovery_summary()`:

| Metric | Formula |
|---|---|
| `recoverable_revenue` | `SUM(transactions.amount * COALESCE(fc.recovery_score, brc.recovery_potential, 0))` for transactions not `SUCCESS` AND `COALESCE(fc.failure_type, brc.failure_type) = 'TEMPORARY'` |
| `permanently_lost_revenue` | `SUM(transactions.amount)` for transactions not `SUCCESS` AND `COALESCE(fc.failure_type, brc.failure_type) = 'PERMANENT'` |

### 4.3 Recovery Score Distribution (NumPy)
Computed in `get_recovery_score_distribution()`:
- Buckets `[0.0, 0.2)`, `[0.2, 0.4)`, `[0.4, 0.6)`, `[0.6, 0.8)`, `[0.8, 1.0]`
- Stats: count, mean, median
- Percentiles: p25, p75, p90 (via NumPy `np.percentile`)

### 4.4 Revenue Impact Aggregates
- `get_revenue_impact_by_gateway()` returns columns: `gateway, recovered_amount, potential_amount, lost_amount, total_amount`.
  - `recovered_amount` = sum(amount) where final_status = `SUCCESS` (with any retries present) OR last retry = `SUCCESS`
  - `lost_amount` = sum(amount) where final_status != `SUCCESS` AND retries exhausted / no success
  - `potential_amount` = recovered_amount + sum(amount * recovery_score) for still-recoverable rows
- `get_revenue_impact_over_time()` returns columns: `period_date, recovered_amount, potential_amount, lost_amount`, grouped by calendar day.

---

## 5. How Tables Are Used Together (Key Joins)

These joins are used by analytics functions in `src/payment_queries.py` and by the Streamlit pages.

### Payment Lifecycle (transaction + retries)
```
transactions t
JOIN payment_retries pr ON t.transaction_id = pr.transaction_id
```

### Failure Context (last response code + classification)
```
transactions t
LEFT JOIN payment_retries latest ... (MAX(attempt_number) per transaction)
LEFT JOIN bank_response_codes brc ON latest.response_code = brc.response_code
LEFT JOIN failure_classifications fc ON t.transaction_id = fc.transaction_id
```

### Prioritized Retry List
Same failure-context join + retry-count subquery + priority-score expression; filtered by max attempts and non-SUCCESS final status.

### Revenue Recovery Aggregates
Same failure-context join aggregated across amount × recovery score, with temporal/gateway groupings.

---

## 6. Excel / CSV Output Schemas

These files are generated by the Streamlit UI from the above DataFrames.

**Retry Analytics (pages/4_Retry_Analytics.py)**
- `retry_success_rate.csv` — `attempt_number, total_attempts, successful, failed, success_rate`
- `retry_timing_distribution.csv` — `window, count`
- `retry_heatmap_success_rates.csv` — `Day, Hour, Success Rate (%)`
- `gateway_retry_performance.csv` — `gateway, total_retries, successful, success_rate`
- `bank_retry_performance.csv` — `bank, total_retries, successful, success_rate`
- `retry_analytics_combined.csv` — pivoted unified view: `Category, Segment, Metric 1, Metric 1 Label, Metric 2, Metric 2 Label, Metric 3, Metric 3 Label`
- `retry_analytics_kpi_summary.csv` — key-value: `KPI, Value`
- `prioritized_transactions_to_retry.csv` — columns listed in §4.1

**Revenue Recovery (pages/5_Revenue_Recovery.py)** — multi-sheet `.xlsx` (engine `openpyxl`):
- `Summary` — KPIs (recoverable, permanently_lost, avg_score, etc.)
- `Revenue Impact Over Time` — `period_date, recovered_amount, potential_amount, lost_amount`
- `Revenue Impact By Gateway` — `gateway, recovered_amount, potential_amount, lost_amount, total_amount`
- `Recovery Score Distribution` — `score_range, count`
- `Recoverable Transactions` — per-transaction rows with recovery score

---

## 7. SMTP Configuration Data (Email Test Send)

Not stored in MySQL; read at runtime from environment variables by `src/email_service.py`.

Vars: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_USE_TLS` (bool).

Transport: `smtplib.SMTP`, TLS started via `starttls()` when enabled.

