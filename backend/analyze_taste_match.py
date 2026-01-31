
import pandas as pd
import os

# 파일 경로
TASTE_CSV = "backend/taste_cleaned.csv"
DRINK_CSV = "backend/drink_info.csv"

def analyze_data_matching():
    if not os.path.exists(TASTE_CSV) or not os.path.exists(DRINK_CSV):
        print(f"❌ 파일을 찾을 수 없습니다.")
        print(f"현재 폴더: {os.getcwd()}")
        return

    # 데이터 로드
    try:
        # 인코딩 자동 감지 (utf-8, cp949, euc-kr)
        try:
            taste_df = pd.read_csv(TASTE_CSV, encoding='utf-8')
        except:
            taste_df = pd.read_csv(TASTE_CSV, encoding='cp949')

        try:
            drink_df = pd.read_csv(DRINK_CSV, encoding='utf-8')
        except:
            drink_df = pd.read_csv(DRINK_CSV, encoding='cp949')
            
    except Exception as e:
        print(f"❌ CSV 로드 오류: {e}")
        return

    print("📊 데이터 로드 완료")
    print(f"- 맛 지표 데이터: {len(taste_df)}개")
    print(f"- 전통주 DB 데이터: {len(drink_df)}개")

    # 이름 기준 매칭 분석
    # 공백 제거 및 소문자 변환으로 매칭률 높이기
    taste_names = set(taste_df['drink_name'].astype(str).str.replace(' ', '').str.lower())
    drink_names = set(drink_df['drink_name'].astype(str).str.replace(' ', '').str.lower())

    # 매칭된 이름
    matched = taste_names.intersection(drink_names)
    unmatched_taste = taste_names - drink_names
    
    match_rate = len(matched) / len(taste_names) * 100

    print("\n🔍 매칭 분석 결과")
    print(f"✅ 매칭 성공: {len(matched)}개 ({match_rate:.1f}%)")
    print(f"❌ 매칭 실패 (DB에 없음): {len(unmatched_taste)}개")

    # 미매칭 샘플 출력
    if unmatched_taste:
        print("\n📝 매칭 실패 샘플 (Top 10):")
        for name in list(unmatched_taste)[:10]:
            print(f"- {name}")
            
    # 대표적인 매칭 성공 사례
    print("\n✅ 매칭 성공 샘플 (Top 5):")
    for name in list(matched)[:5]:
        print(f"- {name}")

if __name__ == "__main__":
    analyze_data_matching()
