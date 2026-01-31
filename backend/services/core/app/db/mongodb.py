from motor.motor_asyncio import AsyncIOMotorClient
import os

class MongoDB:
    client: AsyncIOMotorClient = None

db = MongoDB()

async def get_database():
    if db.client:
        return db.client.get_database("myapp_db")
    return None
async def connect_to_mongo():
    """MongoDB 연결"""
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    if "?" in mongo_url:
        mongo_url += "&authSource=admin"
    else:
        mongo_url += "?authSource=admin"
    db.client = AsyncIOMotorClient(mongo_url)
    print(f"✅ Connected to MongoDB at {mongo_url}")

async def close_mongo_connection():
    """MongoDB 연결 종료"""
    if db.client:
        db.client.close()
        print("❌ Closed MongoDB connection")
