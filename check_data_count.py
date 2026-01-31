
import pymongo
import sys

# Tunnel setup: ssh -L 27018:localhost:27017 ...
# Connecting to myapp_db explicitly to check data
MONGO_URI = "mongodb://root:pass123%23@localhost:27018/myapp_db?authSource=admin&directConnection=true"

def check_data():
    try:
        print("Connecting to MongoDB via Tunnel (localhost:27018)...")
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        
        db = client.myapp_db
        
        collections = db.list_collection_names()
        print(f"Collections in 'myapp_db': {collections}")
        
        target_cols = ['users', 'posts', 'boards', 'community']
        
        print("\n--- Document Counts ---")
        for col_name in collections:
            count = db[col_name].count_documents({})
            print(f"[{col_name}]: {count}")
            
        print("\n-----------------------")
        if 'users' in collections and db.users.count_documents({}) > 0:
            print("✅ USERS Data Exists!")
        else:
            print("❌ USERS Data NOT FOUND!")
            
        if any(c in collections for c in ['posts', 'boards']):
             print("✅ BOARD/POSTS Data Exists!")
        else:
             print("⚠️  BOARD/POSTS Data NOT FOUND (Might be empty if new install)")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_data()
