
import os
from pathlib import Path
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_db_connection():
    """
    Create and return a database connection.
    
    Returns:
        mysql.connector.connection.MySQLConnection: Database connection object, or None if connection fails
    """
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "recoverx")
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None


def close_db_connection(connection):
    """
    Close the database connection if it's open.
    
    Args:
        connection (mysql.connector.connection.MySQLConnection): Database connection object to close
    """
    if connection and connection.is_connected():
        connection.close()
        print("Database connection closed successfully")


def execute_query(query, params=None, fetch=False):
    """
    Execute a SQL query and optionally fetch results.
    
    Args:
        query (str): SQL query to execute
        params (tuple, optional): Parameters for the query
        fetch (bool, optional): Whether to fetch and return results
        
    Returns:
        list or None: Fetched results if fetch=True, None otherwise
    """
    connection = get_db_connection()
    if not connection:
        return None
    
    cursor = None
    results = None
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if fetch:
            results = cursor.fetchall()
        else:
            connection.commit()
            
    except Error as e:
        print(f"Error executing query: {e}")
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        close_db_connection(connection)
    
    return results


def execute_many(query, params_list):
    """
    Execute a SQL query multiple times with different parameters.
    
    Args:
        query (str): SQL query to execute
        params_list (list): List of parameter tuples
        
    Returns:
        bool: True if successful, False otherwise
    """
    connection = get_db_connection()
    if not connection:
        return False
    
    cursor = None
    success = False
    
    try:
        cursor = connection.cursor()
        cursor.executemany(query, params_list)
        connection.commit()
        success = True
    except Error as e:
        print(f"Error executing many queries: {e}")
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        close_db_connection(connection)
    
    return success

