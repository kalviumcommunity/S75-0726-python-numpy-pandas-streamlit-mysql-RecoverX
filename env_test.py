import os
from pathlib import Path
from dotenv import load_dotenv

print("Current working directory:", Path.cwd())
print("Looking for .env at:", Path(__file__).parent / ".env")

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

print("\nEnvironment variables:")
print("DB_HOST:", os.getenv("DB_HOST"))
print("DB_PORT:", os.getenv("DB_PORT"))
print("DB_USER:", os.getenv("DB_USER"))
print("DB_PASSWORD:", os.getenv("DB_PASSWORD")[:10] + "..." if os.getenv("DB_PASSWORD") else "None")
print("DB_NAME:", os.getenv("DB_NAME"))
