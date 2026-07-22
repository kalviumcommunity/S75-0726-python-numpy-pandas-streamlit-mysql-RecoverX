import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Read database details
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "recoverx")

# Path to mysqldump.exe
MYSQLDUMP_PATH = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe"


def backup_database():
    """
    Create a backup (.sql) of the RecoverX database.
    """

    # Create backups folder
    backup_folder = "backups"
    os.makedirs(backup_folder, exist_ok=True)

    # Timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Backup file name
    backup_file = os.path.join(
        backup_folder,
        f"{DB_NAME}_backup_{timestamp}.sql"
    )

    # mysqldump command
    command = [
        MYSQLDUMP_PATH,
        "-h", DB_HOST,
        "-P", DB_PORT,
        "-u", DB_USER,
        f"-p{DB_PASSWORD}",
        "--ssl-mode=REQUIRED",
        DB_NAME
    ]

    try:
        with open(backup_file, "w", encoding="utf-8") as outfile:
            subprocess.run(
                command,
                stdout=outfile,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )

        print("\n===================================")
        print("Backup completed successfully!")
        print("Backup file:")
        print(backup_file)
        print("===================================\n")

    except subprocess.CalledProcessError as e:
        print("\nBackup failed!\n")
        print(e.stderr)


if __name__ == "__main__":
    backup_database()