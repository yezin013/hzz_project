
import pymongo
import sys
from bson import json_util

# Tunnel setup: ssh -L 27018:localhost:27017 ...
MONGO_URI_ADMIN = "mongodb://root:pass123%23@localhost:27018/admin?authSource=admin&directConnection=true"

def check_rs_status():
    try:
        print("Connecting to MongoDB Primary via Tunnel...")
        client = pymongo.MongoClient(MONGO_URI_ADMIN, serverSelectionTimeoutMS=5000)
        
        status = client.admin.command("replSetGetStatus")
        
        print("\n=== Replica Set Status ===")
        print(f"Set Name: {status.get('set')}")
        print(f"Example date: {status.get('date')}")
        
        print("\n--- Members ---")
        for m in status.get('members', []):
            name = m.get('name')
            state = m.get('stateStr')
            optime = m.get('optime', {}).get('ts')
            health = m.get('health')
            print(f"[{state}] {name} (Health: {health}) - Optime: {optime}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_rs_status()
