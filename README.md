#  RecoverX

**RecoverX** is a payment analytics platform that helps businesses understand the complete lifecycle of every payment transaction. It centralizes payment retries, bank response codes, and transaction timestamps into a single system, enabling finance and operations teams to identify recoverable payments, improve retry strategies, and minimize revenue loss through actionable insights.

---

#  Problem Statement        

In many organizations, payment retry records, bank response codes, and transaction timestamps are stored across different systems. Because this information is fragmented, finance and operations teams cannot view the complete journey of a payment transaction.

When a payment fails, it is difficult to determine whether the customer successfully completed the payment after retrying or whether the payment resulted in permanent revenue loss. This lack of visibility makes it challenging to analyze retry performance, identify failure patterns, and make informed business decisions. As a result, businesses face revenue leakage, inefficient retry strategies, and increased manual effort in analyzing payment data.

---

#   Solution

RecoverX provides a centralized analytics platform that integrates payment retries, bank response codes, and transaction timestamps into a unified database. The system reconstructs the complete payment lifecycle for every transaction, automatically classifies payment failures, analyzes retry performance, and identifies potential revenue recovery opportunities.

Through interactive dashboards and real-time analytics, RecoverX enables finance managers, payment analysts, and operations teams to monitor payment health, detect recurring failure patterns, optimize retry strategies, and reduce revenue loss.

---

#  Features

##  Data Integration
- Integrates payment retry records from multiple sources.
- Synchronizes bank response codes and transaction timestamps.
- Maintains a unified payment dataset for analysis.

##  Payment Lifecycle Tracking
- Displays the complete journey of every payment.
- Tracks every retry attempt in chronological order.
- Shows the final payment status (Success or Failure).

##  Failure Classification
- Classifies failures as temporary or permanent.
- Maps failures using bank response codes.
- Identifies transactions with recovery potential.

##  Retry Performance Analytics
- Calculates retry success rates.
- Analyzes retry frequency and timing.
- Identifies ineffective retry patterns.
- Helps optimize retry strategies.
- Builds a **prioritized list of transactions to retry**, ranked by a computed priority score (recovery potential, transaction value, high-value flag, retry count).
- Exports retry analytics data (success rates, timing windows, heatmap values, gateway/bank performance, combined analytics, KPI summary) to CSV.

##  Revenue Recovery Analytics
- Distinguishes recoverable revenue from permanently lost revenue.
- Highlights high-value failed transactions.
- Provides revenue impact insights.
- Shows **recovery score distribution** (buckets, percentiles, average) powered by NumPy.
- Visualizes **revenue impact over time** and by gateway (recovered vs potential vs lost).
- Exports revenue impact workbooks to Excel (multi-sheet `.xlsx`) using `openpyxl`.

##  Alerts & Notifications
- Detects unusually high payment failure rates.
- Alerts users about abnormal bank response code trends.
- Notifies teams about potential revenue loss.
- Provides an **Alerts & Notifications** page (Streamlit) to configure SMTP settings and send a test email.
- Implements an email test sender using `smtplib` (TLS auth configurable via environment variables) in [email_service.py](src/email_service.py).

##  Data Export & Reports
- Per-page CSV export for transaction tables, failure listings, retry analytics, and prioritized retry lists.
- Excel (`.xlsx`) export of revenue impact data with separate sheets for summary, gateway breakdown, time-series, score distribution, and recoverable transactions.
- Retry Analytics combined exports:
  - `retry_analytics_combined.csv` — unified pivot across success attempts, timing windows, gateway, and bank performance.
  - `retry_analytics_kpi_summary.csv` — top-level dashboard KPIs.

##  UI Theming
- Sidebar theme selector (**Dark / Light**) persisted per session in `st.session_state["ui_theme"]`.
- Theme-aware CSS injection for the main app, header, sidebar, and sidebar caption/border colors.
- Defined in [ui_components.py](src/ui_components.py) and applied automatically across all Streamlit pages.

---

#  Tech Stack

| Technology / Library | Purpose |
|------------|---------|
| **Python** | Backend logic, data processing, analytics |
| **Streamlit** | Interactive web application and dashboard |
| **Pandas** | Data cleaning, transformation, analysis, DataFrames for CSV/Excel export |
| **NumPy** | Numerical computations, recovery score percentiles and statistics |
| **Plotly** | Interactive charts (pie, bar, line, heatmap, mixed traces) |
| **MySQL (mysql-connector-python)** | Storage, querying, and management of payment transaction data |
| **openpyxl** | Engine for writing multi-sheet Excel (`.xlsx`) exports |
| **smtplib** (stdlib) | Email notification setup and test email sending |
| **FastAPI + Uvicorn** | Optional REST API layer for transactions, retries, and data imports |
| **pydantic / fastapi** | API data validation (basic auth/API key) |
| **pytest** | Unit tests for analytics and query functions in `payment_queries.py` |

---

#  System Workflow

```
Payment Retry Records
          │
Bank Response Codes
          │
Transaction Timestamps
          │
          ▼
   Data Integration Layer
          │
          ▼
     SQL Database
          │
          ▼
 Data Processing (Python)
          │
          ▼
Payment Lifecycle Tracking
          │
          ▼
Failure Classification
          │
          ▼
Retry Performance Analysis
          │
          ▼
Revenue Recovery Analytics
          │
          ▼
 Streamlit Dashboard
          │
          ▼
 Reports, Insights & Alerts
```

### Workflow Steps

1. Collect payment retry records, bank response codes, and transaction timestamps.
2. Store and synchronize the data in a centralized SQL database.
3. Process and clean the data using Python, Pandas, and NumPy.
4. Reconstruct the complete payment lifecycle for every transaction.
5. Classify payment failures as temporary or permanent and compute recovery scores.
6. Analyze retry success rates, retry patterns, and gateway/bank performance.
7. Compute a **priority score** and build a prioritized retry list for eligible transactions to retry first.
8. Identify recoverable revenue opportunities and visualize revenue impact over time and by gateway.
9. Visualize insights through an interactive Streamlit dashboard (with Dark/Light theme toggle).
10. Generate CSV/Excel reports and send test email notifications (SMTP via `smtplib`).
11. Generate alerts for finance and operations teams.

---

#  Future Enhancements

-  AI-based prediction of payment failures before they occur.
-  Smart retry recommendations based on historical success patterns.
-  Predictive revenue recovery forecasting using machine learning.
-  Bank-wise performance comparison and approval rate analysis.
-  Automated report generation and scheduled email reports (extend the existing smtplib-based test sender in `src/email_service.py`).
-  Multi-currency and multi-payment gateway support.
-  Cloud deployment for improved scalability and availability.
-  Mobile-responsive dashboard for monitoring payment analytics on the go.
-  Custom KPI dashboards with user-defined metrics and filters.

---

# Streamlit Pages Overview

The RecoverX UI is a Streamlit multipage app; all pages live under the `pages/` directory and share layout helpers from [ui_components.py](src/ui_components.py).

| Page | File | Primary Purpose | Key Exports / Features |
|---|---|---|---|
| Dashboard | `pages/0_Dashboard.py` | KPI overview + charts | CSV/Excel export for recent transactions |
| CSV Import | `pages/1_CSV_Import.py` | Import data from files | Validated CSV/JSON upload |
| Payment Lifecycle | `pages/2_Payment_Lifecycle.py` | Transaction-by-transaction journey + retries | Retry history table; per-transaction filters |
| Failure Analysis | `pages/3_Failure_Analysis.py` | Failure distribution by type, response code, gateway, payment method | Pie + bar charts; failed transactions table with CSV export |
| Retry Analytics | `pages/4_Retry_Analytics.py` | Retry success rates, timing windows, heatmap, gateway/bank performance; prioritized retry list | Multiple CSVs: success rates, timing, heatmap, gateway, bank; plus combined analytics + KPI CSVs; prioritized transactions CSV |
| Revenue Recovery | `pages/5_Revenue_Recovery.py` | Recoverable vs lost revenue; recovery score distribution; revenue impact visualizations | Multi-sheet Excel workbook export |
| Alerts & Notifications | `pages/6_Alerts_Notifications.py` | SMTP configuration + test email send | Form fields + test send button wired to `src/email_service.py` |

---

# Environment Variables

Minimum values are declared in `.env.example`. Copy it to `.env` and fill in your own values.

**Database**
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `API_KEY` — shared secret for FastAPI endpoints

**Email (for SMTP test send)**
- `SMTP_HOST` — e.g. `smtp.gmail.com`
- `SMTP_PORT` — e.g. `587`
- `SMTP_USER` — login (often the From address)
- `SMTP_PASSWORD` — app-password or password
- `SMTP_FROM` — email sender display address
- `SMTP_USE_TLS` — `true`/`false` (defaults to `true`)

---

## Database Setup

For detailed instructions on setting up the RecoverX database, please see the [Database Setup Guide](database/DATABASE_SETUP.md).

## API Documentation

For complete API documentation, including how to test endpoints, please see the [API Documentation Guide](API_DOCUMENTATION.md).

---

##  Conclusion

RecoverX transforms fragmented payment data into meaningful business insights by providing complete visibility into payment retries, failure classifications, and revenue recovery opportunities. By enabling data-driven decision-making, the platform helps organizations improve payment success rates, optimize retry strategies, and reduce revenue leakage through a simple and interactive analytics dashboard.