
# Requirements Analysis: RecoverX

## 1. Introduction
RecoverX is a payment analytics platform designed to address the challenge of fragmented payment data across multiple systems. This document outlines the functional and non-functional requirements for the platform.

## 2. Business Requirements
- **BR1**: Centralize payment retry records, bank response codes, and transaction timestamps into a unified system.
- **BR2**: Provide complete visibility into the lifecycle of every payment transaction.
- **BR3**: Classify payment failures as temporary or permanent to identify recoverable revenue.
- **BR4**: Analyze retry performance to optimize retry strategies.
- **BR5**: Reduce revenue leakage through actionable insights and alerts.

## 3. Functional Requirements

### 3.1 Data Integration
- **FR1.1**: The system shall integrate payment retry records from multiple sources.
- **FR1.2**: The system shall synchronize bank response codes and transaction timestamps.
- **FR1.3**: The system shall maintain a unified payment dataset for analysis.

### 3.2 Payment Lifecycle Tracking
- **FR2.1**: The system shall display the complete journey of every payment transaction.
- **FR2.2**: The system shall track every retry attempt in chronological order.
- **FR2.3**: The system shall show the final payment status (Success or Failure).

### 3.3 Failure Classification
- **FR3.1**: The system shall classify failures as temporary or permanent.
- **FR3.2**: The system shall map failures using bank response codes.
- **FR3.3**: The system shall identify transactions with recovery potential.

### 3.4 Retry Performance Analytics
- **FR4.1**: The system shall calculate retry success rates per attempt number.
- **FR4.2**: The system shall analyze retry frequency and timing (avg/median hours between retries, best retry windows).
- **FR4.3**: The system shall identify ineffective retry patterns (per gateway and per bank response description).
- **FR4.4**: The system shall help optimize retry strategies.
- **FR4.5**: The system shall generate a **heatmap** of retry success rates by day of week × hour of day.
- **FR4.6**: The system shall build a **prioritized list of transactions to retry**, ranked by a computed `priority_score` (recovery score, is_high_value flag, transaction amount, retry attempts count).
- **FR4.7**: The system shall export retry analytics datasets to CSV: success rates, timing windows, heatmap values, gateway performance, bank performance, combined analytics, KPI summary, and prioritized retry transactions.

### 3.5 Revenue Recovery Analytics
- **FR5.1**: The system shall distinguish recoverable revenue from permanently lost revenue.
- **FR5.2**: The system shall highlight high-value failed transactions.
- **FR5.3**: The system shall provide revenue impact insights (recovered vs potential vs lost).
- **FR5.4**: The system shall compute and display a **recovery score distribution** (buckets, mean/median, P25/P75/P90 percentiles) powered by NumPy.
- **FR5.5**: The system shall export revenue impact datasets to a multi-sheet Excel workbook (`.xlsx`) via `openpyxl` with sheets for: summary, per-gateway breakdown, time series, recovery score distribution, recoverable transactions.

### 3.6 Alerts & Notifications
- **FR6.1**: The system shall detect unusually high payment failure rates.
- **FR6.2**: The system shall alert users about abnormal bank response code trends.
- **FR6.3**: The system shall notify teams about potential revenue loss.
- **FR6.4**: The system shall provide an **Alerts & Notifications** page with SMTP configuration inputs and a “Send Test Email” button.
- **FR6.5**: The system shall implement an email sending utility using `smtplib` (TLS/auth configurable via environment variables) to support test notifications.

### 3.7 Data Export & Reporting
- **FR7.1**: Every Streamlit page with a data table shall provide CSV export.
- **FR7.2**: Revenue recovery insights shall be exportable to Excel (multiple sheets, `openpyxl` engine).
- **FR7.3**: Retry analytics shall support combined exports (a unified analytics pivot + a KPI summary file).

### 3.8 UI Theming & Accessibility
- **FR8.1**: The Streamlit UI shall support a user-selectable **Dark / Light theme** toggle persisted for the current session.
- **FR8.2**: The theme shall be applied consistently across the main content, header, sidebar, and sidebar helper elements.

## 4. Non-Functional Requirements
- **NFR1**: The system shall use Python, Streamlit, Pandas, NumPy, and MySQL as the tech stack.
- **NFR2**: The system shall provide an interactive dashboard for data visualization.
- **NFR3**: The system shall process and clean data efficiently using Python libraries.
- **NFR4**: The system shall store data in a SQL database.
- **NFR5**: The system shall use `pytest` for backend unit tests and provide at least coverage for analytics functions.
- **NFR6**: Excel exports shall use the `openpyxl` engine (declared in `requirements.txt`).
- **NFR7**: Email test sends shall use the standard-library `smtplib` module with optional TLS; credentials and sender shall be provided via environment variables.
- **NFR8**: Streamlit pages shall use shared layout helpers (`setup_page`, `render_header`, `render_sidebar`, `render_footer`) so theming and branding apply globally.

## 6. Functional Coverage by Page

| Page | Covers Requirements |
|---|---|
| Dashboard (0) | NFR8, FR7.1 (recent transactions CSV/Excel) |
| CSV Import (1) | FR1.1–FR1.3 |
| Payment Lifecycle (2) | FR2.1–FR2.3, FR7.1 |
| Failure Analysis (3) | FR3.1–FR3.3, FR7.1 |
| Retry Analytics (4) | FR4.1–FR4.7, FR7.1, FR7.3 |
| Revenue Recovery (5) | FR5.1–FR5.5, FR7.2 |
| Alerts & Notifications (6) | FR6.1–FR6.5, NFR7 |

## 7. Key Code Modules

| Module | Purpose |
|---|---|
| `src/payment_queries.py` | Centralized MySQL queries for transactions, retries, failure analysis, retry analytics, revenue recovery, and prioritized retry lists. |
| `src/charts.py` | Plotly chart generators for failure/overview/retry/revenue visualizations. |
| `src/ui_components.py` | Shared Streamlit page setup, header/sidebar/footer, and **theme injection** (Dark/Light). |
| `src/email_service.py` | `smtplib`-based test email sender; consumes `SMTP_*` environment variables. |
| `src/db.py` | MySQL connector wrapper (`execute_query`, `execute_many`) used by `payment_queries.py`. |
| `src/numpy_utils.py` | NumPy helpers used for recovery score statistics (percentiles, mean/median) in revenue analytics. |
| `src/api.py` | FastAPI layer for transactions, retries, CSV/JSON import, with basic `API_KEY` auth. |

## 8. Environment Variables

| Group | Vars | Notes |
|---|---|---|
| Database | `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | Required for Streamlit + API |
| API | `API_KEY` | FastAPI endpoints check `X-API-Key` header |
| SMTP | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_USE_TLS` | Used by `src/email_service.py` for test email sends; defaults to TLS on port 587 if not overridden |

## 5. User Roles
- **Finance Managers**: Monitor payment health and revenue recovery opportunities.
- **Payment Analysts**: Analyze retry performance and failure patterns.
- **Operations Teams**: Optimize retry strategies and respond to alerts.

