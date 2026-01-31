
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pymysql
import os
from typing import List

router = APIRouter()

DB_HOST = os.getenv("MARIADB_HOST", "localhost")
DB_PORT = int(os.getenv("MARIADB_PORT", 3306))
DB_USER = os.getenv("MARIADB_USER", "root")
DB_PASS = os.getenv("MARIADB_PASSWORD", "pass123#")
DB_NAME = os.getenv("MARIADB_DB", "drink")

class FairInfo(BaseModel):
    fair_id: int
    fair_year: int
    fair_image_url: str
    fair_homepage_url: str

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

@router.get("/", response_model=List[FairInfo])
def get_fairs():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM fair_info ORDER BY fair_year DESC"
        cursor.execute(query)
        rows = cursor.fetchall()
        
        conn.close()
        return rows
    except Exception as e:
        print(f"DB Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch fair info")
