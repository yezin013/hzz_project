import requests
import json
import sys

# Correct API Endpoint
API_URL = "https://5p1of4jt04.execute-api.ap-northeast-2.amazonaws.com/api/python/search/debug/shops"

def test_debug_shops():
    print(f"\n🧪 [Debug] Fetching ANY drink with real shop data...")
    print(f"   Request: GET {API_URL}")
    
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            samples = data.get('sample_data', [])
            
            print(f"   ✅ Status: 200 OK")
            print(f"   📊 Found Items with Shops: {count}")
            
            if samples:
                print("\n   [Sample Data Found in DB]")
                for item in samples:
                    print(f"   🍶 Drink: {item.get('name')}")
                    shops = item.get('shops', [])
                    print(f"      🛒 Shop Count: {len(shops)}")
                    for s in shops:
                        print(f"         - {s.get('name')} : {s.get('price')}원")
            else:
                print("      - [WARN] No items with selling_shops found in DB!")
                print("      - This means your crawler data might not have been loaded correctly.")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_debug_shops()
