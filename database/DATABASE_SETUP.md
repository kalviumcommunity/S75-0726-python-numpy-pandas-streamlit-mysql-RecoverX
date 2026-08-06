# RecoverX Database Setup Guide

This guide walks you through setting up the RecoverX MySQL database.

---

## Prerequisites
1. MySQL server running locally or remotely
2. MySQL user with CREATE DATABASE, CREATE TABLE, and INSERT privileges
3. Python 3.8+ installed
4. Project dependencies installed (`pip install -r requirements.txt`)

---

## Step 1: Configure Environment Variables

Create a `.env` file in the project root directory and fill in your database credentials:

```env
DB_HOST=your_database_host
DB_PORT=3306
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_NAME=recoverx
API_KEY=recoverx-secret-key
```

If using a remote database (e.g., Aiven, AWS RDS), replace the values with your remote database's connection details.

### Optional: SMTP (for Alerts & Notifications test email send)
To enable the “Send Test Email” button on the Alerts & Notifications page, add these variables to `.env`:

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-login@example.com
SMTP_PASSWORD=your-app-password-or-password
SMTP_FROM=recoverx@example.com
SMTP_USE_TLS=true
```

- `SMTP_USE_TLS` defaults to `true` when unset; set `false` for providers that use implicit SSL or unencrypted localhost SMTP.
- The email test sender is implemented in `src/email_service.py` (standard-library `smtplib`; TLS started with `starttls()` when enabled).

### Excel Export Dependency
Revenue Recovery pages export multi-sheet `.xlsx` workbooks using `openpyxl`. It is already listed in `requirements.txt`; ensure you install it:
```bash
pip install -r requirements.txt
```

---

## Step 2: Create the Database

First, create the database if it doesn't exist:

```sql
CREATE DATABASE IF NOT EXISTS recoverx;
USE recoverx;
```

---

## Step 3: Run the Setup Script

Execute the `database/setup.sql` script to create all required tables and indexes:

### Option A: Using Command Line
```bash
mysql -h DB_HOST -P DB_PORT -u DB_USER -pDB_PASSWORD DB_NAME < database/setup.sql
```

### Option B: Using Python Script (Recommended)
Run the provided `run_schema.py` script to apply the schema:
```bash
python run_schema.py
```

---

## Step 4: Verify the Setup

Check if all tables are created by running the test script:
```bash
python test_db_connection.py
```

You should see a message like:
```
[OK] Database connection successful!
[OK] MySQL version: X.X.X
[OK] Existing tables in recoverx:
  - transactions
  - payment_retries
  - bank_response_codes
  - failure_classifications
  - alert_rules
  - alerts
```

---

## Step 5: Populate Test Data (Optional)

To populate the database with test data, use the `generate_test_data.py` script:
```bash
python generate_test_data.py
```

---

## Troubleshooting

### Connection Issues
- Verify your `.env` file has correct credentials
- Check that MySQL server is running
- Ensure your IP is allowed if using a remote database

### Schema Errors
- Make sure you have sufficient privileges to create tables and indexes
- Check for typos in the SQL script

---

## Backup & Restore

To backup your database, use the `src/backup_database.py` script.
