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
        conn.close()

def get_drinks_by_region(province: str, city: Optional[str] = None):
    """
    Fetches drinks by region (province/city) from MariaDB as fallback.
    """
    conn = get_mariadb_conn()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cursor:
            # Join similar to ETL but filtered by region
            sql = """
                SELECT 
                    d.drink_id, d.drink_name, d.drink_image_url, d.drink_abv, d.drink_volume,
                    d.drink_intro, d.drink_city, 
                    t.type_name,
                    r.province, r.city as region_city
                FROM drink_info d
                LEFT JOIN drink_type t ON d.type_id = t.type_id
                LEFT JOIN drink_region dr ON d.drink_id = dr.drink_id
                LEFT JOIN region r ON dr.region_id = r.id
                WHERE r.province = %s
            """
            params = [province]
            if city:
                sql += " AND r.city = %s"
                params.append(city)
            
            # Limited fallback, no complex sorting
            sql += " LIMIT 100" 
            
            cursor.execute(sql, tuple(params))
            results = cursor.fetchall()
            
            # Map to ES-like structure for frontend
            mapped_results = []
            for row in results:
                # Basic mapping
                prov = row['province']
                region_city = row['region_city']
                
                mapped_results.append({
                    "id": row['drink_id'],
                    "name": row['drink_name'],
                    "image_url": row['drink_image_url'],
                    "type": row['type_name'] or "전통주",
                    "alcohol": f"{row['drink_abv']}%",
                    "price": 0, # DB doesn't have lowest_price easily without more joins
                    "volume": row['drink_volume'],
                    "province": prov,
                    "city": region_city
                })
                
            return mapped_results

            return mapped_results

    except Exception as e:
        print(f"❌ Error fetching region drinks: {e}")
        return []
    finally:
        conn.close()

def get_all_drinks_db(page: int = 1, size: int = 10):
    """
    Fetches all drinks with pagination from MariaDB as fallback.
    """
    conn = get_mariadb_conn()
    if not conn:
        return {"drinks": [], "total": 0}
    
    try:
        with conn.cursor() as cursor:
            offset = (page - 1) * size
            
            # Get Total Count
            cursor.execute("SELECT COUNT(*) as total FROM drink_info")
            total = cursor.fetchone()['total']
            
            # Get Data
            sql = """
                SELECT 
                    d.drink_id, d.drink_name, d.drink_image_url, d.drink_abv, d.drink_volume,
                    d.drink_intro, 
                    t.type_name,
                    r.province, r.city as region_city
                FROM drink_info d
                LEFT JOIN drink_type t ON d.type_id = t.type_id
                LEFT JOIN drink_region dr ON d.drink_id = dr.drink_id
                LEFT JOIN region r ON dr.region_id = r.id
                ORDER BY d.drink_id ASC
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql, (size, offset))
            results = cursor.fetchall()
            
            drinks = []
            for row in results:
                drinks.append({
                    "id": row['drink_id'],
                    "name": row['drink_name'],
                    "image_url": row['drink_image_url'],
                    "type": row['type_name'] or "전통주",
                    "alcohol": f"{row['drink_abv']}%",
                    "price": 0,
                    "volume": row['drink_volume'],
                    "province": row['province'],
                    "city": row['region_city'],
                    "intro": row['drink_intro']
                })
                
            return {
                "drinks": drinks,
                "total": total,
                "page": page,
                "size": size,
                "total_pages": (total + size - 1) // size
            }

    except Exception as e:
        print(f"❌ Error fetching all drinks: {e}")
        return {"drinks": [], "total": 0}
    finally:
        conn.close()
