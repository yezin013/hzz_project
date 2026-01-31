
import pymysql
import json
import os
import datetime

# MariaDB Connection Details
DB_HOST = os.environ.get("MARIADB_HOST", "mariadb.jumak-backend-ns.svc.cluster.local")
DB_PORT = int(os.environ.get("MARIADB_PORT", "3306"))
DB_USER = os.environ.get("MARIADB_USER", "root")
DB_PASS = os.environ.get("MARIADB_PASSWORD", "pass123#")
DB_NAME = os.environ.get("MARIADB_DB", "drink")

OUTPUT_FILE = "/tmp/full_backup.json"

def default_converter(o):
    """JSON serialization for datetime objects"""
    if isinstance(o, datetime.datetime):
        return o.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(o, datetime.date):
        return o.strftime("%Y-%m-%d")
    return str(o)

def backup_all_tables():
    try:
        print(f"🔌 Connecting to MariaDB ({DB_HOST}:{DB_PORT})...")
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = conn.cursor()
        
        # 1. 테이블 목록 조회
        cursor.execute("SHOW TABLES")
        tables = [list(row.values())[0] for row in cursor.fetchall()]
        print(f"📦 Found {len(tables)} tables: {tables}")
        
        full_dump = {}
        
        # 2. 각 테이블 데이터 조회
        for table in tables:
            print(f"📥 Dumping table: {table}...", end=" ")
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            full_dump[table] = rows
            print(f"({len(rows)} rows)")
            
        conn.close()
        
        # 3. JSON 파일로 저장
        print(f"💾 Saving to {OUTPUT_FILE}...")
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(full_dump, f, default=default_converter, ensure_ascii=False, indent=2)
            
        print("✅ Full backup complete!")
        print(f"   Use 'kubectl cp ...' to download {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")

if __name__ == "__main__":
    backup_all_tables()
