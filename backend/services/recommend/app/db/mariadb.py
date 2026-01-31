import os
import pymysql
from typing import Optional, Dict, Any

def get_mariadb_conn():
    """
    Establishes a connection to the MariaDB server.
    Returns a pymysql connection object.
    """
    try:
        # Parse connection details from environment or use defaults
        # Expected format: mysql://user:pass@host:port/db
        # But we'll use individual env vars for simplicity if available, or hardcode for now based on user request
        
        host = os.getenv("MARIADB_HOST", "host.docker.internal")
        port = int(os.getenv("MARIADB_PORT", 3306))
        user = os.getenv("MARIADB_USER", "user")
        password = os.getenv("MARIADB_PASSWORD", "pass123#")
        db_name = os.getenv("MARIADB_DB", "db")

        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor,
            charset='utf8mb4'
        )
        return conn
    except Exception as e:
        print(f"❌ MariaDB Connection Error: {e}")
        return None

def get_liquor_details(drink_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetches liquor details from MariaDB by drink_name.
    """
    conn = get_mariadb_conn()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cursor:
            # Query to fetch details from drink_info table
            # We match by drink_name
            sql = """
                SELECT * FROM drink_info 
                WHERE drink_name = %s
            """
            cursor.execute(sql, (drink_name,))
            result = cursor.fetchone()
            return result
    except Exception as e:
        print(f"❌ Error fetching details for {drink_name}: {e}")
        return None
    finally:
        conn.close()
