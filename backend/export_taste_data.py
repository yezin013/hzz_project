
import pymysql
import pandas as pd
import os
import sys

# MariaDB Connection Details
DB_HOST = os.environ.get("MARIADB_HOST", "mariadb.jumak-backend-ns.svc.cluster.local")
DB_PORT = int(os.environ.get("MARIADB_PORT", "3306"))
DB_USER = os.environ.get("MARIADB_USER", "root")
DB_PASS = os.environ.get("MARIADB_PASSWORD", "pass123#")
DB_NAME = os.environ.get("MARIADB_DB", "drink")

EXPORT_PATH = "/tmp/taste_profile_export.csv"

def export_data():
    try:
        print("🔌 Connecting to MariaDB...")
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        
        sql = """
            SELECT 
                t.*, 
                d.drink_name as original_drink_name 
            FROM taste_profile t
            JOIN drink_info d ON t.drink_id = d.drink_id
        """
        
        print("📥 Fetching data...")
        df = pd.read_sql(sql, conn)
        
        print(f"📊 Rows retrieved: {len(df)}")
        
        print(f"💾 Saving to {EXPORT_PATH}...")
        df.to_csv(EXPORT_PATH, index=False, encoding='utf-8-sig') # Excel compat
        print("✅ Export complete!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    export_data()
