"""
MongoDB Index Creation Script for Performance Optimization
Run this script to create necessary indexes for tasting_notes collection
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def create_indexes():
    # Get MongoDB connection string from environment
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_uri)
    db = client["jumak"]  # Your database name
    
    collection = db["tasting_notes"]
    
    print("Creating indexes for tasting_notes collection...")
    
    # Index for sorting by created_at (descending) - most common query
    await collection.create_index([("created_at", -1)], name="idx_created_at_desc")
    print("✅ Created index: created_at (desc)")
    
    # Compound index for filtering public notes and sorting by date
    await collection.create_index(
        [("is_public", 1), ("created_at", -1)], 
        name="idx_public_created_at"
    )
    print("✅ Created index: is_public + created_at")
    
    # Index for finding notes by liquor_id
    await collection.create_index([("liquor_id", 1)], name="idx_liquor_id")
    print("✅ Created index: liquor_id")
    
    # Index for finding notes by user_id
    await collection.create_index([("user_id", 1)], name="idx_user_id")
    print("✅ Created index: user_id")
    
    # List all indexes
    print("\n📋 Current indexes:")
    async for index in collection.list_indexes():
        print(f"  - {index['name']}: {index.get('key', {})}")
    
    client.close()
    print("\n✅ All indexes created successfully!")

if __name__ == "__main__":
    asyncio.run(create_indexes())
