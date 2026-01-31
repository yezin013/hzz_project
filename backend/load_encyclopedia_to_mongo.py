#!/usr/bin/env python3
"""
백과사전 데이터를 MongoDB에 적재하는 스크립트
JSON 파일 또는 MariaDB에서 데이터를 읽어 MongoDB encyclopedia 컬렉션에 저장
"""
import os
import json
import sys
import pymysql
from pymongo import MongoClient
import urllib.parse

def connect_mongo():
    """MongoDB 연결"""
    hosts = os.getenv("MONGODB_HOSTS", "mongodb-0.mongodb-headless.jumak-db-ns.svc.cluster.local,mongodb-1.mongodb-headless.jumak-db-ns.svc.cluster.local,mongodb-2.mongodb-headless.jumak-db-ns.svc.cluster.local")
    port = os.getenv("MONGODB_PORT", "27017")
    user = os.getenv("MONGODB_USER", "root")
    password = os.getenv("MONGODB_PASSWORD", "pass123#")
    db_name = os.getenv("MONGODB_DB", "admin")
    replica_set = os.getenv("MONGODB_REPLICA_SET", "rs0")
    
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
        print(f"✅ MongoDB 연결 성공!")
        return client["liquor"]
    except Exception as e:
        print(f"❌ MongoDB 연결 실패: {e}")
        return None

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

def load_from_json(file_path):
    """JSON 파일에서 백과사전 데이터 로드"""
    print(f"📦 JSON 파일에서 데이터 로드: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 데이터 변환 (기존 JSON 구조에 맞춰)
    encyclopedia_list = []
    
    if isinstance(data, list):
        for item in data:
            # 이미 올바른 형식인 경우
            if 'name' in item:
                encyclopedia_list.append({
                    'name': item.get('name'),
                    'price': item.get('price'),  # encyclopedia_price_text에 해당
                    'url': item.get('url'),       # encyclopedia_url에 해당
                    'description': item.get('description', ''),
                    'sections': item.get('sections', [])  # 상세 정보
                })
    elif isinstance(data, dict):
        # Dictionary 형식인 경우
        for name, info in data.items():
            encyclopedia_list.append({
                'name': name,
                'price': info.get('price'),
                'url': info.get('url'),
                'description': info.get('description', ''),
                'sections': info.get('sections', [])
            })
    
    print(f"✅ JSON에서 {len(encyclopedia_list)}개 항목 로드 완료")
    return encyclopedia_list

def load_from_mariadb():
    """MariaDB에서 백과사전 데이터 로드"""
    print("📦 MariaDB에서 백과사전 데이터 조회 중...")
    
    try:
        conn = get_mariadb_conn()
        cursor = conn.cursor()
        
        # 백과사전 테이블 확인
        cursor.execute("SHOW TABLES")
        tables = [table[list(table.keys())[0]] for table in cursor.fetchall()]
        
        enc_tables = [t for t in tables if 'encyc' in t.lower() or 'wiki' in t.lower()]
        
        if not enc_tables:
            print("⚠️  MariaDB에 백과사전 테이블이 없습니다.")
            return []
        
        print(f"📋 발견된 테이블: {enc_tables}")
        
        encyclopedia_list = []
        
        # 첫 번째 백과사전 테이블에서 데이터 조회
        table_name = enc_tables[0]
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
        sample = cursor.fetchall()
        
        if sample:
            print(f"\n샘플 데이터 (첫 1개):")
            print(json.dumps(sample[0], ensure_ascii=False, indent=2))
            
            # 전체 데이터 조회
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            for row in rows:
                # 컬럼명에 맞춰 변환 (실제 테이블 구조 확인 필요)
                encyclopedia_list.append({
                    'name': row.get('name') or row.get('drink_name') or row.get('title'),
                    'price': row.get('price') or row.get('encyclopedia_price'),
                    'url': row.get('url') or row.get('link'),
                    'description': row.get('description') or row.get('content') or '',
                    'sections': []
                })
        
        conn.close()
        print(f"✅ MariaDB에서 {len(encyclopedia_list)}개 항목 로드 완료")
        return encyclopedia_list
        
    except Exception as e:
        print(f"❌ MariaDB 조회 실패: {e}")
        return []

def main():
    """메인 실행 로직"""
    print("🚀 백과사전 데이터 적재 시작...")
    print("=" * 60)
    
    # MongoDB 연결
    mongo_db = connect_mongo()
    if not mongo_db:
        print("❌ MongoDB 연결 실패. 종료합니다.")
        sys.exit(1)
    
    # 데이터 로드 (JSON 우선, 없으면 MariaDB)
    json_file = os.getenv("ENCYCLOPEDIA_JSON", "data/encyclopedia.json")
    
    encyclopedia_data = []
    
    if os.path.exists(json_file):
        encyclopedia_data = load_from_json(json_file)
    else:
        print(f"⚠️  JSON 파일 없음: {json_file}")
        print("📦 MariaDB에서 데이터를 가져옵니다...")
        encyclopedia_data = load_from_mariadb()
    
    if not encyclopedia_data:
        print("❌ 적재할 백과사전 데이터가 없습니다.")
        sys.exit(1)
    
    # MongoDB에 적재
    collection = mongo_db["encyclopedia"]
    
    # 기존 데이터 삭제
    print(f"\n🗑️  기존 encyclopedia 컬렉션 삭제 중...")
    collection.delete_many({})
    
    # 새 데이터 삽입
    print(f"📤 {len(encyclopedia_data)}개 문서 삽입 중...")
    result = collection.insert_many(encyclopedia_data)
    
    print(f"✅ {len(result.inserted_ids)}개 문서 삽입 완료!")
    
    # 확인
    count = collection.count_documents({})
    print(f"📊 최종 문서 수: {count}개")
    
    # 샘플 출력
    sample = collection.find_one()
    if sample:
        print("\n📋 샘플 데이터:")
        sample.pop('_id', None)
        print(json.dumps(sample, ensure_ascii=False, indent=2))
    
    print("\n" + "=" * 60)
    print("✅ 백과사전 데이터 적재 완료!")
    print("\n다음 단계: ETL 스크립트 재실행")
    print("  python etl_k8s_final.py")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
