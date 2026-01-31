
import pymongo
import sys
from datetime import datetime

# Tunnel setup: ssh -L 27018:localhost:27017 ...
MONGO_URI = "mongodb://root:pass123%23@localhost:27018/myapp_db?authSource=admin&directConnection=true"

def restore_users():
    try:
        print("Connecting to MongoDB via Tunnel (localhost:27018)...")
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client.myapp_db
        
        # 1. Gather User Info from Tasting Notes
        # We map email -> author_name
        user_map = {}
        
        print("Scanning Tasting Notes for Author Names...")
        notes = db.tasting_notes.find({}, {'user_id': 1, 'author_name': 1})
        for n in notes:
            if 'user_id' in n:
                uid = n['user_id']
                name = n.get('author_name', 'Unknown User')
                # Prioritize existing name over 'Unknown'
                if uid not in user_map or user_map[uid] == 'Unknown User':
                    user_map[uid] = name
                    
        # 2. Gather User Info from Favorites (Fallback)
        print("Scanning Favorites for additional IDs...")
        favs = db.favorites.find({}, {'user_id': 1})
        for f in favs:
            if 'user_id' in f:
                uid = f['user_id']
                if uid not in user_map:
                    user_map[uid] = 'Restored User'

        print(f"\nFound {len(user_map)} users to restore: {user_map}")
        
        # 3. Upsert Users
        restored_count = 0
        for email, name in user_map.items():
            # Check if user already exists
            if db.users.find_one({'email': email}):
                print(f"  - User {email} already exists. Skipping.")
                continue
                
            new_user = {
                "email": email,
                "name": name,
                "hashed_password": "", # No restart possible for password
                "provider": "google" if "gmail" in email else "local",
                "is_active": True,
                "is_superuser": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_restored": True,
                "restoration_note": "Auto-recovered from tasting_notes data"
            }
            
            db.users.insert_one(new_user)
            print(f"  + Restored: {name} ({email})")
            restored_count += 1
            
        print(f"\n✅ User Restoration Complete! Restored {restored_count} profiles.")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    restore_users()
