
import pymongo
import sys

# Tunnel setup: ssh -L 27018:localhost:27017 ...
MONGO_URI = "mongodb://root:pass123%23@localhost:27018/?authSource=admin&directConnection=true"

def check_all():
    try:
        print("Connecting to MongoDB via Tunnel (localhost:27018)...")
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        
        dbs = client.list_database_names()
        print(f"Databases found: {dbs}")
        
        for db_name in dbs:
            if db_name in ['admin', 'local', 'config']:
                continue
            
            print(f"\nScanning DB: [{db_name}]")
            db = client[db_name]
            cols = db.list_collection_names()
            for c in cols:
                count = db[c].count_documents({})
                print(f"  - {c}: {count}")
                
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_all()
