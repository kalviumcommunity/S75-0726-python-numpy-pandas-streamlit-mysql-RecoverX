import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from src.db import get_db_connection, execute_query

print("Testing database connection...")

# Test connection
conn = get_db_connection()
if conn:
    print("[OK] Database connection successful!")
    
    # Test a simple query
    result = execute_query("SELECT VERSION()", fetch=True)
    if result:
        print(f"[OK] MySQL version: {result[0]['VERSION()']}")
    
    # Check if tables exist
    tables = execute_query("SHOW TABLES", fetch=True)
    if tables:
        print(f"[OK] Existing tables in {conn.database}:")
        for table in tables:
            table_name = list(table.values())[0]
            print(f"  - {table_name}")
    
    conn.close()
else:
    print("[FAIL] Database connection failed!")
    print("[INFO] Current configuration (from src/db.py):")
    print("  - DB_HOST: localhost")
    print("  - DB_PORT: 3306") 
    print("  - DB_USER: root")
    print("  - DB_PASSWORD: (empty)")
    print("  - DB_NAME: recoverx")
    print("\n[INFO] To connect, please:")
    print("  1. Create a .env file in the project root with your MySQL credentials (copy .env.example)")
    print("  2. Make sure MySQL server is running")
    print("  3. Create the database 'recoverx' and run database/setup.sql to create tables")

