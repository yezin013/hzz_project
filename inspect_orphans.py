
import pymongo
import sys
import json
from bson import json_util

# Tunnel setup: ssh -L 27018:localhost:27017 ...
MONGO_URI = "mongodb://root:pass123%23@localhost:27018/myapp_db?authSource=admin&directConnection=true"

def inspect_and_repair_plan():
    try:
        print("Connecting to MongoDB via Tunnel (localhost:27018)...")
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client.myapp_db
        
        # 1. Inspect Tasting Notes
        notes = list(db.tasting_notes.find().limit(5))
        favorites = list(db.favorites.find().limit(5))
        
        print("\n=== Sample Tasting Notes ===")
        print(json_util.dumps(notes, indent=2))
        
        print("\n=== Sample Favorites ===")
        print(json_util.dumps(favorites, indent=2))
        
        # 2. Extract Unique User IDs
        user_ids = set()
        
        # From Notes
        all_notes = db.tasting_notes.find({}, {'user_id': 1})
        for n in all_notes:
            if 'user_id' in n:
                user_ids.add(n['user_id'])
                
        # From Favorites
        all_favs = db.favorites.find({}, {'user_id': 1})
        for f in all_favs:
            if 'user_id' in f:
                user_ids.add(f['user_id'])
                
        print(f"\n✅ Found {len(user_ids)} distinct User IDs in surviving data: {user_ids}")
        
        # 3. Check if these users exist
        existing_users = db.users.count_documents({'email': {'$in': list(user_ids)}})
        print(f"📉 Existing User Profiles found: {existing_users}")
        
        if existing_users == 0 and len(user_ids) > 0:
            print("🚀 RECOMMENDATION: Run repair to create placeholder users for these IDs.")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    inspect_and_repair_plan()
