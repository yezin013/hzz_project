import os
from pymongo import MongoClient
import urllib.parse

host = os.getenv("MONGO_HOST", "192.168.0.36")
port = os.getenv("MONGO_PORT", "27017")
user = os.getenv("MONGO_USER", "root")
password = os.getenv("MONGO_PASSWORD")
auth_db = os.getenv("MONGO_AUTH_DB", "admin")

if not password:
    raise ValueError("MONGO_PASSWORD environment variable is not set")

encoded_password = urllib.parse.quote_plus(password)
mongo_url = f"mongodb://{user}:{encoded_password}@{host}:{port}/{auth_db}"

try:
    client = MongoClient(mongo_url, serverSelectionTimeoutMS=2000)
    db = client["liquor"]
    cols = db.list_collection_names()
    print(f"Collections: {cols}")
    
    for col_name in cols:
        doc = db[col_name].find_one()
        print(f"--- Collection: {col_name} ---")
        print(doc)

except Exception as e:
    print(f"Error: {e}")
