import os
from pymongo import MongoClient
import urllib.parse

host = "192.168.0.36"
port = "27017"
user = "root"
password = "pass123#"
auth_db = "admin"

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
