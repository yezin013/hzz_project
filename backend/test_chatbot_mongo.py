import requests
import json
import sys

# Correct API Endpoint for Chatbot Service 
API_URL = "https://5p1of4jt04.execute-api.ap-northeast-2.amazonaws.com/api/python/chatbot/debug/mongo/shops"

def test_mongo_debug(drink_name="감홍로"):
    print(f"\n🧪 [Debug] Retrieving MongoDB data for: {drink_name}")
    
    # Collections to try
    collections = ["products", "crawling_results", "liquor_products", "items"]
    
    found_any = False
    
    for col in collections:
        print(f"\n🔍 Checking collection: '{col}'...")
        url = f"{API_URL}?name={drink_name}&collection={col}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                
                if status == "Found":
                    found_any = True
                    print(f"   ✅ FOUND in '{col}'!")
                    
                    doc = data.get('data')
                    shops = doc.get('selling_shops', [])
                    print(f"   🛒 Selling Shops Count: {len(shops)}")
                    
                    if shops:
                        for i, s in enumerate(shops):
                            name = s.get('name')
                            price = s.get('price')
                            print(f"      {i+1}. Name: {name} | Price: {price}")
                    else:
                         print("      (Shops array is empty or key 'selling_shops' missing)")
                         # Check alternative keys
                         mall = doc.get('mall_name')
                         lprice = doc.get('lprice')
                         link = doc.get('link')
                         
                         print(f"      👉 mall_name: {mall}")
                         if mall:
                              print(f"         (Hex: {mall.encode('utf-8').hex()})")
                         print(f"      👉 lprice: {lprice}")
                         print(f"      👉 link: {link}") # Check link too
                         
                         print(f"      KEYS in DOC: {list(doc.keys())}")
                    
                    # Do NOT return, continue to check other collections
                    # return 
                else:
                     print(f"   ❌ Not found in '{col}'")
                     # Print available cols only once
                     if 'collections_available' in data and col == collections[0]:
                         print(f"   (Available: {data.get('collections_available')})")

            else:
                print(f"   ❌ API Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Network/Script Error: {e}")

    if not found_any:
        print("\n❌ Could not find the drink in ANY of the tested collections.")

if __name__ == "__main__":
    test_mongo_debug("감홍로")
