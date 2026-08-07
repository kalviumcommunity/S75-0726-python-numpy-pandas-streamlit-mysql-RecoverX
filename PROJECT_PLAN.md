# RecoverX Project Plan – 10 Days, Individual Assignments

## Team: Abishek, Reshma, Tejal, Yogesh, Dharshni

---

## Overview
This plan covers all remaining features for RecoverX, a payment analytics platform, with clear individual assignments and role labels to complete the project by Day 10.

---

## Day 1: Project Kickoff & Database Finalization
- **Goal:** Ensure database is fully set up with test data
- **Tasks by Person:**
  - **Abishek (Database):** Verify database schema against documentation and add any missing indexes/constraints
  - **Reshma (Database):** Run test data generation script to populate all database tables
  - **Tejal (Database):** Create a database backup script
  - **Yogesh (Backend/Testing):** Write tests for database connection and basic CRUD operations
  - **Dharshni (Documentation):** Document database setup steps

---

## Day 2: Data Integration & API Enhancements
- **Goal:** Complete API endpoints and data integration
- **Tasks by Person:**
  - **Abishek (Backend):** Add pagination to all GET API endpoints
  - **Reshma (Backend):** Add bulk data import endpoints (CSV/JSON)
  - **Tejal (Backend):** Implement authentication middleware for API (basic auth/API key)
  - **Yogesh (Backend):** Add request validation using Pydantic models
  - **Dharshni (Backend/Testing/Documentation):** Add Swagger/OpenAPI documentation details and test all API endpoints with Postman/curl

---

## Day 3: Payment Lifecycle Page Development
- **Goal:** Build interactive Payment Lifecycle page
- **Tasks by Person:**
  - **Abishek (Frontend):** Add transaction search/filter (by transaction ID, customer ID, date range, status)
  - **Reshma (Frontend):** Display transaction timeline with retry attempts
  - **Tejal (Frontend):** Add charts (transaction success/failure over time, retry attempts distribution) using Plotly
  - **Yogesh (Backend/Frontend):** Integrate page with backend to fetch data
  - **Dharshni (Frontend):** Add export functionality (CSV/Excel) for transaction data

---

## Day 4: Failure Analysis Page Development
- **Goal:** Build Failure Analysis page
- **Tasks by Person:**
  - **Abishek (Frontend):** Display failure distribution by type (TEMPORARY vs PERMANENT)
  - **Reshma (Frontend):** Show failure breakdown by bank response code, gateway, payment method
  - **Tejal (Backend):** Add failure classification logic
  - **Yogesh (Frontend):** Build interactive table of failed transactions with filtering
  - **Dharshni (Frontend):** Add visualizations (pie/bar charts for failure causes)

---

## Day 5: Retry Analytics Page Development
- **Goal:** Build Retry Analytics page
- **Tasks by Person:**
  - **Abishek (Backend + Frontend):** Calculate retry success rates per attempt number and display them
  - **Reshma (Backend + Frontend):** Analyze retry timing (average time between retries, best retry windows) and display
  - **Tejal (Frontend):** Add retry performance by gateway/bank
  - **Yogesh (Frontend):** Build heatmap/chart for retry success by time of day/day of week
  - **Dharshni (Frontend + Backend/Testing):** Add export for retry analytics and write unit tests for analytics functions

---

## Day 6: Revenue Recovery Page Development
- **Goal:** Complete Revenue Recovery page
- **Tasks by Person:**
  - **Abishek (Backend + Frontend):** Calculate total recoverable revenue, permanently lost revenue and display
  - **Reshma (Frontend):** Highlight high-value failed transactions with recovery potential
  - **Tejal (Backend + Frontend):** Add recovery score distribution using NumPy utilities and display
  - **Yogesh (Frontend):** Build prioritized list of transactions to retry
  - **Dharshni  (Frontend):** Add revenue impact visualizations and export to Excel

---

## Day 7: Alerts & Notifications Page Development
- **Goal:** Build Alerts page
- **Tasks by Person:**
  - **Abishek (Frontend):** Implement alert rule creation/editing/deletion UI
  - **Reshma (Backend):** Build alert generation logic based on rules
  - **Tejal (Frontend):** Display active alerts with severity levels (LOW/MEDIUM/HIGH/CRITICAL)
  - **Yogesh (Frontend):** Add mark-as-resolved functionality and alert history
  - **Dharshni (Backend):** Add email notification mockup/setup (using smtplib for testing)

---

## Day 8: Dashboard & CSV Import Enhancements
- **Goal:** Polish Dashboard and CSV Import pages
- **Tasks by Person:**
  - **Abishek (Frontend):** Add real-time key metrics to dashboard (total txns, success rate, revenue recovered, etc.)
  - **Reshma (Backend + Frontend):** Build CSV import with validation
  - **Tejal (Frontend):** Add drag-and-drop file upload to CSV Import page
  - **Yogesh (Frontend):** Add recent alerts and top failures to dashboard
  - **Dharshni (Frontend):** Add theme customization (light/dark mode) for Streamlit UI

---

## Day 9: Integration, Testing & Bug Fixes
- **Goal:** End-to-end testing and bug fixing
- **Tasks by Person:**
  - **Abishek (Testing):** Perform end-to-end integration testing of all pages and API
  - **Reshma (Testing):** Write unit tests for all backend functions
  - **Tejal (Testing):** Run performance tests on database queries and API endpoints
  - **Yogesh (Bug Fixing):** Fix all reported bugs and cross-browser/device testing
  - **Dharshni (Documentation):** Update all documentation

---

## Day 10: Final Deployment & Presentation Preparation
- **Goal:** Prepare for delivery and present the project
- **Tasks by Person:**
  - **Abishek (Deployment/Demo):** Finalize deployment setup (local/remote server) and create demo video
  - **Reshma (Documentation):** Prepare user manual and FAQ document
  - **Tejal (Code Review):** Do final code review and clean up
  - **Yogesh (Testing/Database):** Run final full test suite and backup database
  - **Dharshni (Presentation):** Create project presentation slides and practice demo

---

## Final Checks (End of Day 10)
- ✅ All features working
- ✅ All tests passing
- ✅ Documentation complete
- ✅ Demo ready
- ✅ Single entrypoint: root `app.py` is the RecoverX landing page; Dashboard lives in `pages/0_Dashboard.py` only
- ✅ Dashboard query: `get_payment_method_amounts(start_date, end_date)` returns sum(amount) grouped by payment_method
- ✅ Revenue Recovery query: `get_high_value_failed_transactions(limit, min_amount, start_date, end_date)` ordered by (recovery_score * amount) DESC
- ✅ Retry Analytics query: `get_ineffective_retry_patterns(threshold_success_rate)` finds banks/gateways/attempts below threshold
- ✅ Revenue Recovery summary: `get_revenue_recovery_summary(start_date, end_date)` used by alert rules
- ✅ Alerts engine: `generate_alerts_from_rules()` supports `revenue_loss` rule type (triggers when recoverable_revenue >= threshold)
- ✅ Convenience wrapper: `generate_all_alerts(start_date, end_date)` runs default rules and returns active alerts + count
