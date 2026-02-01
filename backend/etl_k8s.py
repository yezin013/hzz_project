#!/usr/bin/env python3
"""
K8s 환경용 ETL 스크립트
MariaDB + MongoDB + Elasticsearch 통합
Encyclopedia JSON 파일 없이 동작
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
        user=os.getenv("MARIADB_USER", ""),
        password=os.getenv("MARIADB_PASSWORD", ""),
        database=os.getenv("MARIADB_DB", "drink"),
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4'
    )

def connect_mongo():
    """MongoDB Replica Set 연결"""
    hosts = os.getenv("MONGODB_HOSTS", "mongodb-0.mongodb-headless.jumak-db-ns.svc.cluster.local,mongodb-1.mongodb-headless.jumak-db-ns.svc.cluster.local,mongodb-2.mongodb-headless.jumak-db-ns.svc.cluster.local")
    port = os.getenv("MONGODB_PORT", "27017")
    user = os.getenv("MONGODB_USER", "")
    password = os.getenv("MONGODB_PASSWORD", "")
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
    password = os.getenv("ELASTICSEARCH_PASSWORD", "")
    
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
    """인덱스 생성 및 매핑 설정"""
    if es.indices.exists(index=INDEX_NAME):
        print(f"⚠️ 인덱스 {INDEX_NAME} 이미 존재. 삭제 후 재생성...")
        es.indices.delete(index=INDEX_NAME)

    settings = {
        "analysis": {
            "analyzer": {
                "korean_analyzer": {
                    "type": "standard",
                    "stopwords": "_none_"
                }
            }
        }
    }
    
    mapping = {
        "properties": {
            "drink_id": {"type": "integer"},
            "name": {
                "type": "text", 
                "analyzer": "korean_analyzer",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "type": {"type": "keyword"},
            "alcohol": {"type": "float"}, 
            "volume": {"type": "text"},
            "intro": {"type": "text", "analyzer": "korean_analyzer"},
            "description": {"type": "text", "analyzer": "korean_analyzer"}, 
            "image_url": {"type": "keyword"},
            "awards": {"type": "text", "analyzer": "korean_analyzer", "fields": {"keyword": {"type": "keyword"}}},
            "season": {"type": "keyword"},
            "cocktails": {
                "type": "nested",
                "properties": {
                    "name": {"type": "text"},
                    "recipe": {"type": "text"}
                }
            },
            "foods": {"type": "text", "analyzer": "korean_analyzer"},
            "ingredients": {"type": "text", "analyzer": "korean_analyzer"}, 
            "lowest_price": {"type": "long"},
            "price_source": {"type": "keyword"},
            "price_is_reference": {"type": "boolean"},
            "encyclopedia_price_text": {"type": "text"},
            "encyclopedia_url": {"type": "keyword"},
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
                    "name": {"type": "text", "analyzer": "korean_analyzer"},
                    "address": {"type": "text"},
                    "contact": {"type": "keyword"},
                    "homepage": {"type": "keyword"}
                }
            }
        }
    }
    
    es.indices.create(index=INDEX_NAME, body={"settings": settings, "mappings": mapping})
    print(f"✅ 인덱스 생성 완료: {INDEX_NAME}")


# 표준 지역 명칭 리스트
VALID_PROVINCES = [
    "서울특별시", "부산광역시", "대구광역시", "인천광역시", "광주광역시",
    "대전광역시", "울산광역시", "세종특별자치시",
    "경기도", "강원도", "충청북도", "충청남도", "전라북도", "전라남도", "경상북도", "경상남도", "제주도"
]

def fix_region_province(prov, city):
    """
    지역 명칭 표준화 및 데이터 보정
    예: '경기도 마포구' -> '서울특별시'
        '강원특별자치도' -> '강원도' (프론트엔드 필터 기준)
    """
    if not prov:
        return prov
        
    prov = prov.strip()
    
    # 1. 잘못된 데이터 보정 (특정 케이스)
    if city:
        city = city.strip()
        # 경기도 마포구 같은 잘못된 데이터 수정 (마포구는 서울)
        if "마포구" in city:
            return "서울특별시"
    
    # 2. 특별자치도 등 명칭 매핑 (프론트엔드 호환성)
    mapping = {
        "강원특별자치도": "강원도",
        "전북특별자치도": "전라북도",
        "제주특별자치도": "제주도",
        "서울": "서울특별시", "서울시": "서울특별시",
        "부산": "부산광역시", "부산시": "부산광역시",
        "대구": "대구광역시", "대구시": "대구광역시",
        "인천": "인천광역시", "인천시": "인천광역시",
        "광주": "광주광역시", "광주시": "광주광역시",
        "대전": "대전광역시", "대전시": "대전광역시",
        "울산": "울산광역시", "울산시": "울산광역시",
        "세종": "세종특별자치시", "세종시": "세종특별자치시",
        "경기": "경기도", 
        "강원": "강원도",
        "충북": "충청북도", "충남": "충청남도",
        "전북": "전라북도", "전남": "전라남도",
        "경북": "경상북도", "경남": "경상남도",
        "제주": "제주도"
    }
    
    if prov in mapping:
        return mapping[prov]
        
    # 3. 이미 올바른 명칭 확인
    if prov in VALID_PROVINCES:
        return prov
        
    return prov

def run_etl():
    """ETL 메인 로직"""
    print("🚀 K8s ETL 시작...")
    
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
    mongo_products_col = mongo_db["products"] if mongo_db is not None else None
    mongo_seasons_col = mongo_db["seasons"] if mongo_db is not None else None
    
    season_map = {}
    if mongo_seasons_col is not None:
        print("📦 Season 데이터 로드 중...")
        for doc in mongo_seasons_col.find():
            d_name = doc.get("name")
            d_season = doc.get("season")
            if d_name and d_season:
                season_map[d_name.strip()] = d_season
        print(f"✅ Season 데이터 {len(season_map)}개 로드 완료")
    
    # 4. MariaDB 기본 데이터 조회
    with mariadb.cursor() as cursor:
        print("📦 MariaDB 전통주 데이터 조회 중...")
        sql = """
            SELECT 
                d.drink_id, d.drink_name, d.drink_image_url, d.drink_intro, 
                d.drink_abv, d.drink_volume, d.drink_city, 
                t.type_name,
                r.province, r.city as region_city,
                b.brewery_name, b.brewery_address, b.brewery_contact, b.brewery_homepage
            FROM drink_info d
            LEFT JOIN drink_type t ON d.type_id = t.type_id
            LEFT JOIN drink_region dr ON d.drink_id = dr.drink_id
            LEFT JOIN region r ON dr.region_id = r.id
            LEFT JOIN brewery_info b ON d.brewery_id = b.brewery_id
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
        
        # 안주 정보
        print("📦 안주 정보 조회 중...")
        cursor.execute("""
            SELECT b.drink_id, f.name as food_name 
            FROM drink_pairing_food_bridge b
            JOIN pairing_food f ON b.food_id = f.id
        """)
        food_map = {}
        for row in cursor.fetchall():
            food_map.setdefault(row['drink_id'], []).append(row['food_name'])
        print(f"✅ 안주 {len(food_map)}개 조회 완료")
        
        # 판매처 정보
        print("📦 판매처 정보 조회 중...")
        cursor.execute("""
            SELECT b.drink_id, s.name, b.price, s.url
            FROM shop_drinks_bridge b
            JOIN menu_shop s ON b.shop_id = s.shop_id
        """)
        shop_map = {}
        for row in cursor.fetchall():
            shop_map.setdefault(row['drink_id'], []).append({
                "name": row['name'],
                "price": row['price'],
                "url": row['url']
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
        if mongo_products_col is not None:
            price_doc = mongo_products_col.find_one({"liquor_id": d_id}, sort=[("lprice", 1)])
            if not price_doc:
                price_doc = mongo_products_col.find_one({"drink_name": name}, sort=[("lprice", 1)])
            if price_doc:
                lprice = int(price_doc.get('lprice', 0))
                if lprice > 0:
                    price_source = 'lowest_price'
        
        # MariaDB 판매처에서 최저가 fallback
        if lprice == 0:
            shops = shop_map.get(d_id, [])
            if shops:
                min_price = min([s['price'] for s in shops if s['price'] > 0], default=0)
                if min_price > 0:
                    lprice = min_price
                    price_source = 'lowest_price'
        
        # 지역 정보
        prov = drink['province']
        city = drink['region_city']
        if not city and drink['drink_city']:
            city = drink['drink_city']
            if not prov and ' ' in city:
                prov = city.split(' ')[0]
        
        # 지역 명칭 보정
        prov = fix_region_province(prov, city)
        
        # Season 매핑
        s_val = season_map.get(name.strip())
        
        # Brewery 데이터
        brewery_data = None
        if drink.get('brewery_name'):
            brewery_data = {
                "name": drink.get('brewery_name', ''),
                "address": drink.get('brewery_address', ''),
                "contact": drink.get('brewery_contact', ''),
                "homepage": drink.get('brewery_homepage', '')
            }
        
        doc = {
            "drink_id": d_id,
            "name": name,
            "type": drink['type_name'] or "기타",
            "alcohol": abv,
            "volume": drink['drink_volume'],
            "intro": drink['drink_intro'],
            "description": drink['drink_intro'],  # Encyclopedia 없이 intro 사용
            "image_url": drink['drink_image_url'],
            "awards": [],
            "season": s_val,
            "cocktails": cocktail_map.get(d_id, []),
            "foods": food_map.get(d_id, []),
            "ingredients": "",
            "lowest_price": lprice,
            "price_source": price_source,
            "price_is_reference": False,
            "encyclopedia_price_text": None,
            "encyclopedia_url": None,
            "selling_shops": shop_map.get(d_id, []),
            "encyclopedia": [],
            "region": {
                "province": prov,
                "city": city
            },
            "brewery": brewery_data
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
