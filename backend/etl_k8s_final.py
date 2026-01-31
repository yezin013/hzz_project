#!/usr/bin/env python3
"""
K8s 환경용 최종 ETL 스크립트
MariaDB + MongoDB + Elasticsearch 통합
Nori, ICU, Phonetic 플러그인 사용
백과사전 데이터 포함
"""
import os
import sys
import pymysql
import json
from pymongo import MongoClient
from elasticsearch import Elasticsearch
import urllib3
urllib3.disable_warnings()

# Elasticsearch Index Name
INDEX_NAME = "liquor_integrated"

def get_mariadb_conn():
    """MariaDB 연결"""
    return pymysql.connect(
        host=os.getenv("MARIADB_HOST", "211.46.52.153"),
        port=int(os.getenv("MARIADB_PORT", 15432)),
        user=os.getenv("MARIADB_USER", "team3"),
        password=os.getenv("MARIADB_PASSWORD", "Gkrtod1@"),
        database=os.getenv("MARIADB_DB", "drink"),
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4'
    )

def connect_mongo():
    """MongoDB Replica Set 연결"""
    hosts = os.getenv("MONGODB_HOSTS", "mongodb-0.mongodb-headless.jumak-db-ns.svc.cluster.local,mongodb-1.mongodb-headless.jumak-db-ns.svc.cluster.local,mongodb-2.mongodb-headless.jumak-db-ns.svc.cluster.local")
    port = os.getenv("MONGODB_PORT", "27017")
    user = os.getenv("MONGODB_USER", "root")
    password = os.getenv("MONGODB_PASSWORD", "pass123#")
    db_name = os.getenv("MONGODB_DB", "admin")
    replica_set = os.getenv("MONGODB_REPLICA_SET", "rs0")
    
    import urllib.parse
    encoded_password = urllib.parse.quote_plus(password)
    
    host_list = [host.strip() for host in hosts.split(",")]
    hosts_string = ",".join([f"{host}:{port}" for host in host_list])
    
    replica_url = f"mongodb://{user}:{encoded_password}@{hosts_string}/{db_name}?replicaSet={replica_set}"
    
    try:
        client = MongoClient(
            replica_url,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            retryWrites=True
        )
        client.admin.command('ping')
        print(f"✅ MongoDB Replica Set 연결 성공: {host_list}")
        return client["liquor"]
    except Exception as e:
        print(f"❌ MongoDB 연결 실패: {e}")
        return None

def get_es_client():
    """Elasticsearch 클라이언트 생성"""
    host = os.getenv("ELASTICSEARCH_HOSTS", "elasticsearch.jumak-db-ns.svc.cluster.local")
    port = int(os.getenv("ELASTICSEARCH_PORT", 9200))
    username = os.getenv("ELASTICSEARCH_USERNAME", "elastic")
    password = os.getenv("ELASTICSEARCH_PASSWORD", "pass123#")
    
    es = Elasticsearch(
        [f"https://{host}:{port}"],
        basic_auth=(username, password),
        verify_certs=False,
        ssl_show_warn=False,
        request_timeout=30
    )
    
    if es.ping():
        print(f"✅ Elasticsearch 연결 성공: {host}:{port}")
        return es
    else:
        print("❌ Elasticsearch 연결 실패")
        return None

def setup_index(es):
    """인덱스 생성 및 매핑 설정 (Nori, ICU, Phonetic 플러그인 사용)"""
    if es.indices.exists(index=INDEX_NAME):
        print(f"⚠️ 인덱스 {INDEX_NAME} 이미 존재. 삭제 후 재생성...")
        es.indices.delete(index=INDEX_NAME)

    settings = {
        "analysis": {
            "tokenizer": {
                "nori_user_tokenizer": {
                    "type": "nori_tokenizer",
                    "decompound_mode": "mixed"
                }
            },
            "filter": {
                "icu_normalizer_filter": {
                    "type": "icu_normalizer",
                    "name": "nfc"
                },
                "phonetic_filter": {
                    "type": "phonetic",
                    "encoder": "metaphone",
                    "replace": False
                }
            },
            "analyzer": {
                "nori_analyzer": {
                    "type": "custom",
                    "tokenizer": "nori_user_tokenizer",
                    "filter": ["lowercase", "trim", "icu_normalizer_filter"]
                },
                "nori_phonetic_analyzer": {
                    "type": "custom",
                    "tokenizer": "nori_user_tokenizer",
                    "filter": ["lowercase", "trim", "icu_normalizer_filter", "phonetic_filter"]
                },
                "romanized_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"]
                }
            }
        }
    }
    
    mapping = {
        "properties": {
            "drink_id": {"type": "integer"},
            "name": {
                "type": "text", 
                "analyzer": "nori_analyzer",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "romanized": {
                        "type": "text",
                        "analyzer": "romanized_analyzer"
                    },
                    "phonetic": {
                        "type": "text",
                        "analyzer": "nori_phonetic_analyzer"
                    }
                }
            },
            "type": {"type": "keyword"},
            "alcohol": {"type": "float"}, 
            "volume": {"type": "text"},
            "intro": {"type": "text", "analyzer": "nori_analyzer"},
            "description": {"type": "text", "analyzer": "nori_analyzer"}, 
            "image_url": {"type": "keyword"},
            "awards": {"type": "text", "analyzer": "nori_analyzer"},
            "season": {"type": "keyword"},
            "foods": {"type": "text", "analyzer": "nori_analyzer"},
            "ingredients": {"type": "text", "analyzer": "nori_analyzer"}, 
            "lowest_price": {"type": "long"},
            "price_source": {"type": "keyword"},
            "price_is_reference": {"type": "boolean"},
            "encyclopedia_price_text": {"type": "text"},
            "encyclopedia_url": {"type": "keyword"},
            "cocktails": {
                "type": "nested",
                "properties": {
                    "name": {"type": "text"},
                    "recipe": {"type": "text"}
                }
            },
            "selling_shops": {
                "type": "nested",
                "properties": {
                    "name": {"type": "text"},
                    "price": {"type": "long"},
                    "url": {"type": "keyword"}
                }
            },
            "region": {
                "properties": {
                    "province": {"type": "keyword"},
                    "city": {"type": "keyword"}
                }
            },
            "brewery": {
                "properties": {
                    "name": {"type": "text", "analyzer": "nori_analyzer"},
                    "address": {"type": "text"},
                    "contact": {"type": "keyword"},
                    "homepage": {"type": "keyword"}
                }
            },
            "taste": {
                "properties": {
                    "sweetness": {"type": "integer"},
                    "sourness": {"type": "integer"},
                    "freshness": {"type": "integer"},
                    "body": {"type": "integer"},
                    "balance": {"type": "integer"},
                    "aroma": {"type": "integer"}
                }
            }
        }
    }
    
    es.indices.create(index=INDEX_NAME, body={"settings": settings, "mappings": mapping})
    print(f"✅ 인덱스 생성 완료: {INDEX_NAME}")

def run_etl():
    """ETL 메인 로직"""
    print("🚀 K8s ETL 시작 (with Plugins)...")
    
    # 1. 연결
    mariadb = get_mariadb_conn()
    mongo_db = connect_mongo()
    es = get_es_client()
    
    if not mariadb or not es:
        print("❌ DB/ES 연결 실패")
        return
    
    # 2. 인덱스 설정
    setup_index(es)
    
    # 3. MongoDB 데이터 사전 로드
    mongo_products = mongo_db["products"]
    mongo_seasons = mongo_db["seasons"]
    
    # 백과사전 컬렉션 확인 (is not None으로 명시적 체크)
    collection_names = mongo_db.list_collection_names()
    mongo_encyclopedia = mongo_db["encyclopedia"] if "encyclopedia" in collection_names else None
    
    season_map = {}
    if mongo_db is not None:
        print("📦 Season 데이터 로드 중...")
        for doc in mongo_seasons.find():
            d_name = doc.get("name")
            d_season = doc.get("season")
            if d_name and d_season:
                season_map[d_name.strip()] = d_season
        print(f"✅ Season 데이터 {len(season_map)}개 로드 완료")
    
    # 백과사전 데이터 매핑
    encyclopedia_map = {}
    if mongo_encyclopedia is not None:
        print("📦 Encyclopedia 데이터 로드 중...")
        for doc in mongo_encyclopedia.find():
            name = doc.get("name", "").strip()
            if name:
                encyclopedia_map[name] = {
                    "price_text": doc.get("price"),
                    "url": doc.get("url"),
                    "description": doc.get("description", "")
                }
        print(f"✅ Encyclopedia {len(encyclopedia_map)}개 로드 완료")
    
    # 4. MariaDB 기본 데이터 조회
    with mariadb.cursor() as cursor:
        print("📦 MariaDB 전통주 데이터 조회 중...")
        sql = """
            SELECT 
                d.drink_id, d.drink_name, d.drink_image_url, d.drink_intro, 
                d.drink_abv, d.drink_volume, d.drink_city, 
                t.type_name,
                r.province, r.city as region_city,
                b.brewery_name, b.brewery_address, b.brewery_contact, b.brewery_homepage,
                tp.sweetness, tp.sourness, tp.freshness, tp.body, tp.balance, tp.aroma
            FROM drink_info d
            LEFT JOIN drink_type t ON d.type_id = t.type_id
            LEFT JOIN drink_region dr ON d.drink_id = dr.drink_id
            LEFT JOIN region r ON dr.region_id = r.id
            LEFT JOIN brewery_info b ON d.brewery_id = b.brewery_id
            LEFT JOIN taste_profile tp ON d.drink_id = tp.drink_id
        """
        cursor.execute(sql)
        drinks = cursor.fetchall()
        print(f"✅ 전통주 {len(drinks)}개 조회 완료")
        
        # 칵테일 정보
        print("📦 칵테일 정보 조회 중...")
        cursor.execute("""
            SELECT b.drink_id, c.cocktail_title, c.cocktail_recipe
            FROM cocktail_base_bridge b
            JOIN cocktail_info c ON b.cocktail_id = c.cocktail_id
        """)
        cocktail_map = {}
        for row in cursor.fetchall():
            cocktail_map.setdefault(row['drink_id'], []).append({
                "name": row['cocktail_title'],
                "recipe": row['cocktail_recipe']
            })
        print(f"✅ 칵테일 {len(cocktail_map)}개 조회 완료")
        
        # 안주 정보 (정확한 컬럼명: food_id, food_name)
        print("📦 안주 정보 조회 중...")
        cursor.execute("""
            SELECT b.drink_id, f.food_name 
            FROM drink_pairing_food_bridge b
            JOIN pairing_food f ON b.food_id = f.food_id
        """)
        food_map = {}
        for row in cursor.fetchall():
            food_map.setdefault(row['drink_id'], []).append(row['food_name'])
        print(f"✅ 안주 {len(food_map)}개 조회 완료")
        
        # 판매처 정보 (shop_drinks_bridge만 사용, url 없음)
        print("📦 판매처 정보 조회 중...")
        cursor.execute("""
            SELECT drink_id, shop_name, menu_price
            FROM shop_drinks_bridge
        """)
        shop_map = {}
        for row in cursor.fetchall():
            price = row['menu_price'] if row['menu_price'] is not None else 0
            shop_map.setdefault(row['drink_id'], []).append({
                "name": row['shop_name'],
                "price": price,
                "url": None
            })
        print(f"✅ 판매처 {len(shop_map)}개 조회 완료")
    
    # 5. Elasticsearch Bulk Insert
    print("📤 Elasticsearch 적재 중...")
    actions = []
    
    for drink in drinks:
        d_id = drink['drink_id']
        name = drink['drink_name']
        
        # 도수 파싱
        try:
            abv = float(str(drink['drink_abv']).replace('%', ''))
        except:
            abv = 0.0
        
        # MongoDB에서 최저가 조회
        lprice = 0
        price_source = None
        if mongo_db is not None:
            price_doc = mongo_products.find_one({"liquor_id": d_id}, sort=[("lprice", 1)])
            if not price_doc:
                price_doc = mongo_products.find_one({"drink_name": name}, sort=[("lprice", 1)])
            if price_doc:
                lprice = int(price_doc.get('lprice', 0))
                if lprice > 0:
                    price_source = 'lowest_price'
        
        # MariaDB 판매처에서 최저가 fallback
        if lprice == 0:
            shops = shop_map.get(d_id, [])
            if shops:
                # None 값 필터링
                valid_prices = [s['price'] for s in shops if s['price'] is not None and s['price'] > 0]
                if valid_prices:
                    lprice = min(valid_prices)
                    price_source = 'lowest_price'
        
        # 지역 정보
        prov = drink['province']
        city = drink['region_city']
        if not city and drink['drink_city']:
            city = drink['drink_city']
            if not prov and ' ' in city:
                prov = city.split(' ')[0]
        
        # Season 매핑
        s_val = season_map.get(name.strip())
        
        # 백과사전 정보 병합
        encyclopedia_info = encyclopedia_map.get(name.strip(), {})
        description = encyclopedia_info.get("description") or drink['drink_intro']
        
        # Brewery 데이터
        brewery_data = None
        if drink.get('brewery_name'):
            brewery_data = {
                "name": drink.get('brewery_name', ''),
                "address": drink.get('brewery_address', ''),
                "contact": drink.get('brewery_contact', ''),
                "homepage": drink.get('brewery_homepage', '')
            }
            
        # Taste Profile 데이터
        taste_data = None
        # 하나라도 있으면 데이터가 있는 것으로 간주
        if drink.get('sweetness') is not None: 
            taste_data = {
                "sweetness": drink.get('sweetness', 0) if drink.get('sweetness') is not None else 0,
                "sourness": drink.get('sourness', 0) if drink.get('sourness') is not None else 0,
                "freshness": drink.get('freshness', 0) if drink.get('freshness') is not None else 0,
                "body": drink.get('body', 0) if drink.get('body') is not None else 0,
                "balance": drink.get('balance', 0) if drink.get('balance') is not None else 0,
                "aroma": drink.get('aroma', 0) if drink.get('aroma') is not None else 0
            }
        
        doc = {
            "drink_id": d_id,
            "name": name,
            "type": drink['type_name'] or "기타",
            "alcohol": abv,
            "volume": drink['drink_volume'],
            "intro": drink['drink_intro'],
            "description": description,
            "image_url": drink['drink_image_url'],
            "awards": [],
            "season": s_val,
            "price_source": price_source,
            "price_is_reference": False,
            "encyclopedia_price_text": encyclopedia_info.get("price_text"),
            "encyclopedia_url": encyclopedia_info.get("url"),
            "cocktails": cocktail_map.get(d_id, []),
            "foods": food_map.get(d_id, []),
            "ingredients": "",
            "lowest_price": lprice,
            "selling_shops": shop_map.get(d_id, []),
            "encyclopedia": [],
            "region": {
                "province": prov,
                "city": city
            },
            "brewery": brewery_data,
            "taste": taste_data
        }
        
        action = {"index": {"_index": INDEX_NAME, "_id": str(d_id)}}
        actions.append(json.dumps(action))
        actions.append(json.dumps(doc))
        
        if len(actions) >= 200:  # 100개씩 bulk
            es.bulk(body="\n".join(actions))
            actions = []
            print(f"  📊 진행 중... ({d_id}/{len(drinks)})")
    
    if actions:
        es.bulk(body="\n".join(actions))
    
    print("✅ ETL 완료!")
    
    # 6. 결과 확인
    count = es.count(index=INDEX_NAME)
    print(f"📊 최종 적재 문서 수: {count['count']}")

if __name__ == "__main__":
    try:
        run_etl()
    except Exception as e:
        print(f"❌ ETL 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
