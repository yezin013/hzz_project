
import os
import pymysql
import json

# Connection defaults (matching mariadb.py)
host = os.getenv("MARIADB_HOST", "localhost")
port = int(os.getenv("MARIADB_PORT", 3306))
user = os.getenv("MARIADB_USER", "user")
password = os.getenv("MARIADB_PASSWORD", "pass123#")
db_name = os.getenv("MARIADB_DB", "db")

try:
    print(f"Connecting to {host}:{port} as {user}...")
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor
    )
    print("Connected!")
    
    with conn.cursor() as cursor:
        cursor.execute("DESCRIBE drink_info")
        columns = cursor.fetchall()
        print(json.dumps(columns, indent=2, default=str))
        
    conn.close()

except Exception as e:
    print(f"Error: {e}")
