
import pymysql
import pandas as pd
import os
import sys

# MariaDB Connection Details (from AWS Secrets Manager via External Secrets)
DB_HOST = os.environ.get("MARIADB_HOST", "mariadb.jumak-backend-ns.svc.cluster.local")
DB_PORT = int(os.environ.get("MARIADB_PORT", "3306"))
DB_USER = os.environ.get("MARIADB_USER", "root")
DB_PASS = os.environ.get("MARIADB_PASSWORD", "pass123#")  # 실제: MARIADB_PASSWORD
DB_NAME = os.environ.get("MARIADB_DB", "drink")           # 실제: MARIADB_DB

CSV_PATH = "/tmp/taste_cleaned.csv"  # CSV 파일은 /tmp에 복사됨

def create_taste_profile_table(cursor):
    """맛 지표 테이블 생성 (기존 테이블 삭제 후 재생성)"""
    cursor.execute("DROP TABLE IF EXISTS taste_profile")
    print("🗑️  기존 taste_profile 테이블 삭제 (스키마 갱신)")

    create_table_sql = """
    CREATE TABLE taste_profile (
        id INT AUTO_INCREMENT PRIMARY KEY,
        drink_id INT,
        drink_name VARCHAR(255),
        sweetness INT,      -- 단맛 (0-5)
        sourness INT,       -- 신맛 (0-5)
        freshness INT,      -- 청량감 (0-5)
        body INT,           -- 바디감 (0-5)
        balance INT,        -- 균형감 (0-5)
        aroma INT,          -- 향 (0-5)
        season VARCHAR(20), -- 계절
        UNIQUE KEY unique_drink_name (drink_name),
        FOREIGN KEY (drink_id) REFERENCES drink_info(drink_id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    cursor.execute(create_table_sql)
    print("✅ taste_profile 테이블 생성/확인 완료")

import json

# 파일 경로
ENCYCLOPEDIA_JSON = "/tmp/지식백과 비정형.json"

def load_aliases():
    """지식백과 데이터에서 별칭(name <-> entry_name) 맵 생성"""
    if not os.path.exists(ENCYCLOPEDIA_JSON):
        print(f"⚠️ 별칭 사전 파일 없음: {ENCYCLOPEDIA_JSON}")
        return {}
        
    print("📖 지식백과 별칭 데이터 로드 중...")
    try:
        with open(ENCYCLOPEDIA_JSON, 'rb') as f:
            raw_data = f.read()
            
        encodings = ['utf-8', 'cp949', 'euc-kr']
        json_data = None
        
        for enc in encodings:
            try:
                json_data = json.loads(raw_data.decode(enc))
                break
            except:
                continue
                
        alias_map = {}
        if json_data:
            for item in json_data:
                n1 = item.get('name')
                n2 = item.get('entry_name')
                
                if n1 and n2 and n1 != n2:
                    # 서로가 서로의 별칭
                    alias_map[n1.replace(' ', '').replace('_', '')] = n2
                    alias_map[n2.replace(' ', '').replace('_', '')] = n1
                    
        print(f"✅ 별칭 {len(alias_map)}개 로드 완료")
        return alias_map
    except Exception as e:
        print(f"❌ 별칭 로드 실패: {e}")
        return {}

def match_drink_names(cursor, taste_df):
    """CSV의 drink_name을 drink_info의 drink_id와 매칭 (유연한 검색 + 별칭)"""
    print("\n🔍 전통주 이름 매칭 중...")
    
    alias_map = load_aliases()
    
    matched_data = []
    unmatched = []
    
    for _, row in taste_df.iterrows():
        original_name = row['drink_name']
        
        # 1. 원본 그대로 검색
        search_names = [original_name]
        
        # 2. 언더바를 공백으로 변환 (모월_청 -> 모월 청)
        search_names.append(original_name.replace('_', ' '))
        
        # 3. 언더바/공백 모두 제거 (모월_청 -> 모월청)
        clean_key = original_name.replace('_', '').replace(' ', '')
        search_names.append(clean_key)
        
        # 4. 괄호 앞부분만 검색 (와인 (드라이) -> 와인)
        if '(' in original_name:
             search_names.append(original_name.split('(')[0].strip().replace('_', ' '))

        # 5. 단위/접미사 제거 (12도, 12%, ml 등) -> 숫자는 유지 (문경바람 백자 25)
        suffixes = ['도', '%', 'ml', 'mL', 'alc', 'Alc', 'Vol', 'vol']
        clean_name = original_name.replace('_', ' ')
        for suffix in suffixes:
            if suffix in clean_name:
                clean_name = clean_name.replace(suffix, '').strip()
        search_names.append(clean_name)
        
        # 6. 특수문자/숫자 제거 후 검색 (문경바람 오크 40 -> 문경바람 오크)
        import re
        no_digits = re.sub(r'[\d\.,]', '', clean_name).strip() # 숫자, 마침표, 쉼표 제거
        search_names.append(no_digits)
        
        # 7. 별칭 추가 (지식백과)
        if clean_key in alias_map:
            alias = alias_map[clean_key]
            search_names.append(alias)
            # 별칭의 정제된 형태도 추가
            search_names.append(alias.replace(' ', ''))
            print(f"💡 별칭 시도: {original_name} -> {alias}")
        
        # 중복 제거 (순서 유지!)
        seen = set()
        ordered_names = []
        for n in search_names:
            if n not in seen and n.strip():
                ordered_names.append(n)
                seen.add(n)
        
        found = False
        for name in ordered_names:
            if not name.strip(): continue # 빈 문자열 건너뛰기
            
            # MariaDB에서 이름으로 검색
            # (LIKE 순서 중요: 정확히 포함된 것을 찾기 위해)
            cursor.execute("""
                SELECT drink_id, drink_name 
                FROM drink_info 
                WHERE REPLACE(drink_name, ' ', '') LIKE %s
                OR drink_name LIKE %s
                LIMIT 1
            """, (f"%{name.replace(' ', '')}%", f"%{name}%"))

            
            result = cursor.fetchone()
            
            if result:
                matched_data.append({
                    'drink_id': result['drink_id'],
                    'drink_name': result['drink_name'],
                    'sweetness': int(row['sweet']) if pd.notna(row['sweet']) else 0,
                    'sourness': int(row['sour']) if pd.notna(row['sour']) else 0,
                    'freshness': int(row['fresh']) if pd.notna(row['fresh']) else 0,
                    'body': int(row['body']) if pd.notna(row['body']) else 0,
                    'balance': int(row['balance']) if pd.notna(row['balance']) else 0,
                    'aroma': int(row['aroma']) if pd.notna(row['aroma']) else 0,
                    'season': row['season'] if pd.notna(row['season']) else None
                })
                print(f"✅ 매칭 ({original_name}): {name} → {result['drink_name']} (ID: {result['drink_id']})")
                found = True
                break
        
        if not found:
            unmatched.append(original_name)
            print(f"❌ 미매칭: {original_name}")

    
    if unmatched:
        print(f"\n⚠️  매칭 실패: {len(unmatched)}개")
        print("미매칭 목록 (Top 20):", unmatched[:20])
    
    print(f"\n📊 매칭 완료: {len(matched_data)}/{len(taste_df)}개")
    return matched_data

def load_taste_profile():
    try:
        print("🔌 Connecting to MariaDB...")
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = conn.cursor()

        # 1. 테이블 생성
        create_taste_profile_table(cursor)
        conn.commit()

        # 2. CSV 읽기
        print(f"\n📖 Reading CSV from {CSV_PATH}...")
        if not os.path.exists(CSV_PATH):
            print(f"❌ 파일을 찾을 수 없습니다: {CSV_PATH}")
            print(f"현재 디렉토리: {os.getcwd()}")
            sys.exit(1)
            
        df = pd.read_csv(CSV_PATH)
        print(f"📊 총 {len(df)}개의 맛 지표 데이터 발견")

        # 3. 전통주 이름 매칭
        matched_data = match_drink_names(cursor, df)
        
        if not matched_data:
            print("⚠️  매칭된 데이터가 없습니다!")
            conn.close()
            return

        # 4. 데이터 적재
        print(f"\n🔄 Upserting {len(matched_data)} taste profiles...")
        
        insert_sql = """
        INSERT INTO taste_profile (
            drink_id, drink_name, sweetness, sourness, freshness, 
            body, balance, aroma, season
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            drink_id=VALUES(drink_id),
            sweetness=VALUES(sweetness),
            sourness=VALUES(sourness),
            freshness=VALUES(freshness),
            body=VALUES(body),
            balance=VALUES(balance),
            aroma=VALUES(aroma),
            season=VALUES(season)
        """
        
        values = [
            (
                data['drink_id'], data['drink_name'], data['sweetness'],
                data['sourness'], data['freshness'], data['body'],
                data['balance'], data['aroma'], data['season']
            )
            for data in matched_data
        ]
        
        cursor.executemany(insert_sql, values)
        conn.commit()
        print(f"✅ {len(matched_data)}개의 맛 지표 데이터 적재 완료!")
        
        # 5. 결과 확인
        cursor.execute("SELECT COUNT(*) as count FROM taste_profile")
        count = cursor.fetchone()['count']
        print(f"\n📊 taste_profile 테이블 총 레코드 수: {count}")
        
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    load_taste_profile()
