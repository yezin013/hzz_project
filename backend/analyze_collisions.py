
import pandas as pd
import json
import re
import os

# 파일 경로
TASTE_CSV = "backend/taste_cleaned.csv"
DRINK_CSV = "backend/drink_info.csv"
ENCYCLOPEDIA_JSON = "backend/지식백과 비정형.json"

def normalize_name(name):
    """이름 정규화"""
    return str(name).replace(" ", "").replace("_", "").strip()

def load_aliases():
    """지식백과 별칭 로드"""
    if not os.path.exists(ENCYCLOPEDIA_JSON):
        return {}
    
    try:
        with open(ENCYCLOPEDIA_JSON, 'rb') as f:
            raw_data = f.read()
        
        # 인코딩 처리
        for enc in ['utf-8', 'cp949', 'euc-kr']:
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
                    alias_map[normalize_name(n1)] = n2
                    alias_map[normalize_name(n2)] = n1
        return alias_map
    except:
        return {}

def check_collisions():
    print("🚀 데이터 충돌 분석 시작...\n")
    
    # 데이터 로드
    try:
        taste_df = pd.read_csv(TASTE_CSV)
        # drink_info.csv 로드 (인코딩 처리)
        try:
            drink_df = pd.read_csv(DRINK_CSV, encoding='utf-8')
        except:
            drink_df = pd.read_csv(DRINK_CSV, encoding='cp949')
            
        print(f"📊 맛 데이터: {len(taste_df)}개")
        print(f"📦 DB 데이터: {len(drink_df)}개")
    except Exception as e:
        print(f"❌ 파일 로드 실패: {e}")
        return

    alias_map = load_aliases()
    
    # DB 데이터를 검색하기 좋게 전처리
    # 1. Normalized Name -> ID 매핑
    db_lookup = {}
    
    # 2. Original Name -> ID 매핑 (정확도 우선)
    db_exact_lookup = {}
    
    for _, row in drink_df.iterrows():
        d_id = row['drink_id']
        d_name = str(row['drink_name'])
        
        db_exact_lookup[d_name] = d_id
        db_exact_lookup[d_name.replace(' ', '')] = d_id
        
        # Normalized
        norm_name = normalize_name(d_name)
        if norm_name not in db_lookup:
            db_lookup[norm_name] = []
        db_lookup[norm_name].append(d_id)

    # 매칭 시뮬레이션
    matched_map = {} # drink_id -> [list of csv names]
    
    for _, row in taste_df.iterrows():
        original_name = row['drink_name']
        found_id = None
        
        # 검색 후보군 생성 (load_taste_profile.py 로직과 유사)
        candidates = [original_name]
        candidates.append(original_name.replace('_', ' '))
        candidates.append(original_name.replace('_', '').replace(' ', ''))
        
        if '(' in original_name:
             candidates.append(original_name.split('(')[0].strip().replace('_', ' '))
             
        suffixes = ['도', '%', 'ml', 'mL', 'alc', 'Alc', 'Vol', 'vol']
        clean_name = original_name.replace('_', ' ')
        for suffix in suffixes:
            if suffix in clean_name:
                clean_name = clean_name.replace(suffix, '').strip()
        candidates.append(clean_name)
        
        no_digits = re.sub(r'[\d\.,]', '', clean_name).strip()
        candidates.append(no_digits)
        
        clean_key = normalize_name(original_name)
        if clean_key in alias_map:
            alias = alias_map[clean_key]
            candidates.append(alias)
            candidates.append(alias.replace(' ', ''))

        # 매칭 시도
        for cand in candidates:
            if not cand.strip(): continue
            
            # 1. Exact/Space-stripped match
            if cand in db_exact_lookup:
                found_id = db_exact_lookup[cand]
                break
            
            cand_norm = normalize_name(cand)
            if cand_norm in db_exact_lookup:
                 found_id = db_exact_lookup[cand_norm]
                 break
            
            # Simple contains search fallback (simplified for local check)
            # 로컬에서는 like 검색이 어려우므로 정확/정규화 매칭 위주로 확인
            
        if found_id:
            if found_id not in matched_map:
                matched_map[found_id] = []
            matched_map[found_id].append(original_name)

    # 충돌 분석 (하나의 ID에 여러 CSV 이름이 매칭된 경우)
    collisions = {k: v for k, v in matched_map.items() if len(v) > 1}
    
    print(f"\n⚡ 충돌 발생 ID 수: {len(collisions)}개 (총 {sum(len(v) for v in collisions.values())}개 이름이 매핑됨)")
    print("\n📝 주요 충돌 사례 (Top 10):")
    
    count = 0
    for d_id, names in collisions.items():
        # DB 이름 찾기
        db_name_row = drink_df[drink_df['drink_id'] == d_id]
        db_name = db_name_row.iloc[0]['drink_name'] if not db_name_row.empty else "Unknown"
        
        print(f"\n🆔 ID {d_id} ({db_name})")
        for n in names:
            print(f"   - {n}")
        
        count += 1
        if count >= 10: break

if __name__ == "__main__":
    check_collisions()
