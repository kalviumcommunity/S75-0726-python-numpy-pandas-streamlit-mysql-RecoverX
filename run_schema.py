import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    port=int(os.getenv("DB_PORT"))
)

cursor = conn.cursor()

with open("database/setup.sql", "r") as f:
    sql_script = f.read()

# Split on semicolons to run multiple statements
for statement in sql_script.split(";"):
    statement = statement.strip()
    if statement:
        cursor.execute(statement)

conn.commit()
cursor.close()
conn.close()
print("Schema applied successfully!")