"""
챗봇 기능 테스트 스크립트
- 가드레일, 날씨, 감정, 시간/요일 기능 테스트
"""
import asyncio
import aiohttp
import json
from datetime import datetime

# API 엔드포인트 (EKS)
API_URL = "https://hanzanzu.cloud/api/python/chatbot/chat"

# 테스트 케이스 정의
TEST_CASES = [
    # 1. 가드레일 테스트 (5개)
    {"category": "가드레일", "message": "오늘 주식 어때?", "expected": "거절"},
    {"category": "가드레일", "message": "내일 날씨 알려줘", "expected": "거절"},
    {"category": "가드레일", "message": "파이썬 코드 짜줘", "expected": "거절"},
    {"category": "가드레일", "message": "맛있는 라면 추천해줘", "expected": "거절"},
    {"category": "가드레일", "message": "막걸리 추천해줘", "expected": "술 추천"},
    
    # 2. 날씨 기반 테스트 (5개) - 서울 좌표
    {"category": "날씨", "message": "오늘 같은 날씨에 어울리는 술 추천해줘", "lat": 37.5665, "lon": 126.9780, "expected": "날씨 언급"},
    {"category": "날씨", "message": "비 오는 날 마시기 좋은 술", "lat": 37.5665, "lon": 126.9780, "expected": "막걸리"},
    {"category": "날씨", "message": "추운 겨울에 어울리는 술", "lat": 37.5665, "lon": 126.9780, "expected": "고도수"},
    {"category": "날씨", "message": "더운 여름에 마시기 좋은 술", "lat": 37.5665, "lon": 126.9780, "expected": "저도수"},
    {"category": "날씨", "message": "지금 기온에 맞는 술 추천해줘", "lat": 37.5665, "lon": 126.9780, "expected": "날씨 언급"},
    
    # 3. 감정 기반 테스트 (5개)
    {"category": "감정", "message": "오늘 너무 슬퍼서 한잔 하고 싶어", "expected": "고도수"},
    {"category": "감정", "message": "기분 좋아서 가볍게 한잔 하고 싶어", "expected": "저도수"},
    {"category": "감정", "message": "스트레스 받아서 독한 술 마시고 싶어", "expected": "고도수"},
    {"category": "감정", "message": "축하할 일이 있어서 술 추천해줘", "expected": "술 추천"},
    {"category": "감정", "message": "외로운 밤에 마시기 좋은 술", "expected": "술 추천"},
    
    # 4. 시간/요일 테스트 (5개)
    {"category": "시간", "message": "오늘 저녁에 마시기 좋은 술 추천해줘", "expected": "술 추천"},
    {"category": "시간", "message": "점심에 가볍게 마실 술 있어?", "expected": "술 추천"},
    {"category": "시간", "message": "금요일 저녁에 어울리는 술", "expected": "술 추천"},
    {"category": "시간", "message": "월요일 퇴근 후 마시기 좋은 술", "expected": "술 추천"},
    {"category": "시간", "message": "주말에 마시기 좋은 술 추천해줘", "expected": "술 추천"},
]

async def test_chatbot(session, test_case, index):
    """단일 테스트 케이스 실행"""
    payload = {
        "message": test_case["message"]
    }
    
    # 날씨 테스트의 경우 좌표 추가
    if "lat" in test_case:
        payload["latitude"] = test_case["lat"]
        payload["longitude"] = test_case["lon"]
    
    try:
        async with session.post(API_URL, json=payload, timeout=30) as response:
            if response.status == 200:
                data = await response.json()
                answer = data.get("answer", "")
                drinks = data.get("drinks", [])
                
                # 결과 분석
                result = {
                    "번호": index + 1,
                    "카테고리": test_case["category"],
                    "질문": test_case["message"],
                    "기대값": test_case["expected"],
                    "응답": answer[:200] + "..." if len(answer) > 200 else answer,
                    "추천술수": len(drinks),
                    "추천술": [d.get("name") for d in drinks[:3]] if drinks else [],
                    "성공여부": "✅" if len(answer) > 10 else "❌"
                }
                
                # 가드레일 체크
                if test_case["expected"] == "거절":
                    if "술" not in test_case["message"] and len(drinks) == 0:
                        result["성공여부"] = "✅"
                    elif "술" in test_case["message"] and len(drinks) > 0:
                        result["성공여부"] = "✅"
                
                return result
            else:
                return {
                    "번호": index + 1,
                    "카테고리": test_case["category"],
                    "질문": test_case["message"],
                    "기대값": test_case["expected"],
                    "응답": f"HTTP Error: {response.status}",
                    "추천술수": 0,
                    "추천술": [],
                    "성공여부": "❌"
                }
    except Exception as e:
        return {
            "번호": index + 1,
            "카테고리": test_case["category"],
            "질문": test_case["message"],
            "기대값": test_case["expected"],
            "응답": f"Error: {str(e)}",
            "추천술수": 0,
            "추천술": [],
            "성공여부": "❌"
        }

async def run_tests():
    """모든 테스트 실행"""
    print(f"🧪 챗봇 기능 테스트 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📍 테스트 대상: {API_URL}")
    print(f"📊 총 테스트 수: {len(TEST_CASES)}\n")
    
    results = []
    
    async with aiohttp.ClientSession() as session:
        for i, test_case in enumerate(TEST_CASES):
            print(f"[{i+1}/{len(TEST_CASES)}] {test_case['category']}: {test_case['message'][:30]}...")
            result = await test_chatbot(session, test_case, i)
            results.append(result)
            print(f"  → {result['성공여부']} 추천술: {result['추천술']}")
            await asyncio.sleep(1)  # Rate limiting
    
    return results

def generate_report(results):
    """마크다운 보고서 생성"""
    report = f"""# 챗봇 기능 테스트 보고서

**테스트 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**테스트 대상**: {API_URL}  
**총 테스트**: {len(results)}건

---

## 📊 요약

| 카테고리 | 테스트 수 | 성공 | 성공률 |
|----------|----------|------|--------|
"""
    
    # 카테고리별 통계
    categories = {}
    for r in results:
        cat = r["카테고리"]
        if cat not in categories:
            categories[cat] = {"total": 0, "success": 0}
        categories[cat]["total"] += 1
        if r["성공여부"] == "✅":
            categories[cat]["success"] += 1
    
    for cat, stats in categories.items():
        rate = (stats["success"] / stats["total"]) * 100
        report += f"| {cat} | {stats['total']} | {stats['success']} | {rate:.0f}% |\n"
    
    total_success = sum(1 for r in results if r["성공여부"] == "✅")
    total_rate = (total_success / len(results)) * 100
    report += f"| **전체** | **{len(results)}** | **{total_success}** | **{total_rate:.0f}%** |\n"
    
    report += "\n---\n\n## 📝 상세 결과\n\n"
    
    # 카테고리별 상세 결과
    for cat in ["가드레일", "날씨", "감정", "시간"]:
        cat_results = [r for r in results if r["카테고리"] == cat]
        if cat_results:
            report += f"### {cat} 테스트\n\n"
            report += "| # | 질문 | 기대 | 추천술 | 결과 |\n"
            report += "|---|------|------|--------|------|\n"
            for r in cat_results:
                drinks_str = ", ".join(r["추천술"][:2]) if r["추천술"] else "없음"
                question = r["질문"][:25] + "..." if len(r["질문"]) > 25 else r["질문"]
                report += f"| {r['번호']} | {question} | {r['기대값']} | {drinks_str} | {r['성공여부']} |\n"
            report += "\n"
    
    report += "---\n\n## 💬 응답 샘플\n\n"
    
    # 각 카테고리별 1개씩 응답 샘플
    for cat in ["가드레일", "날씨", "감정", "시간"]:
        cat_results = [r for r in results if r["카테고리"] == cat]
        if cat_results:
            sample = cat_results[0]
            report += f"### {cat} 응답 예시\n\n"
            report += f"**질문**: {sample['질문']}\n\n"
            report += f"**응답**: {sample['응답']}\n\n"
    
    return report

async def main():
    results = await run_tests()
    report = generate_report(results)
    
    # 보고서 저장
    report_path = r"C:\Users\hi-12\.gemini\antigravity\brain\0b5df4ad-997a-4137-92a7-4b47c669b863\chatbot_test_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n📄 보고서 저장: {report_path}")
    print(report)

if __name__ == "__main__":
    asyncio.run(main())
