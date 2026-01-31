
import pymongo
import sys
from bson import json_util

# Tunnel setup: ssh -L 27018:localhost:27017 ...
MONGO_URI_ADMIN = "mongodb://root:pass123%23@localhost:27018/admin?authSource=admin&directConnection=true"

def get_host_info():
    try:
        print("Connecting to MongoDB Primary via Tunnel...")
        client = pymongo.MongoClient(MONGO_URI_ADMIN, serverSelectionTimeoutMS=5000)
        
        info = client.admin.command("hostInfo")
        print("\n=== Host Info ===")
        print(json_util.dumps(info, indent=2))

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    get_host_info()
