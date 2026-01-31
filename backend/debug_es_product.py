import sys
import os
import boto3
import json

# Add service directory to path to find app module
sys.path.append(os.path.join(os.path.dirname(__file__), 'services', 'search'))

# --- Helper to fetch secrets directly ---
def setup_es_env_from_secrets():
    print("🔑 Fetching credentials from AWS Secrets Manager...")
    try:
        # Assuming the secret name used in serverless.yml
        secret_name = "jumak/backend/prod" 
        region_name = "ap-northeast-2"

        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )
        
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            secret_dict = json.loads(secret)
            
            # Set environment variables for es_client to use
            if 'ELASTICSEARCH_HOSTS' in secret_dict:
                os.environ['ELASTICSEARCH_HOSTS'] = secret_dict['ELASTICSEARCH_HOSTS']
                print("   ✅ ELASTICSEARCH_HOSTS set.")
            if 'ELASTICSEARCH_USERNAME' in secret_dict:
                os.environ['ELASTICSEARCH_USERNAME'] = secret_dict['ELASTICSEARCH_USERNAME']
            if 'ELASTICSEARCH_PASSWORD' in secret_dict:
                os.environ['ELASTICSEARCH_PASSWORD'] = secret_dict['ELASTICSEARCH_PASSWORD']
            
    except Exception as e:
        print(f"   ❌ Failed to fetch secrets: {e}")

# Call setup before importing check_es_client which might init things
setup_es_env_from_secrets()

from app.utils.es_client import get_es_client

def debug_product_data(drink_name):
    es = get_es_client()
    if not es:
        print("❌ ES Connection Failed")
        return

    query = {
        "query": {
            "match": {
                "name": {
                    "query": drink_name,
                    "operator": "and"
                }
            }
        }
    }

    print(f"🔎 Searching for: {drink_name}")
    resp = es.search(index="products_liquor", body=query)
    
    hits = resp['hits']['hits']
    print(f"📊 Hits found: {len(hits)}")
    
    if hits:
        source = hits[0]['_source']
        # print(json.dumps(source, indent=2, ensure_ascii=False))
        
        shops = source.get('selling_shops', [])
        print(f"\n🛒 Selling Shops Count: {len(shops)}")
        for shop in shops:
            print(f" - {shop}")
    else:
        print("❌ No documents found.")

if __name__ == "__main__":
    debug_product_data("도문대작 생막걸리")
