# RAG 평가 테스트 실행 스크립트
import json
import requests
from golden_dataset import test_cases

API_BASE = "http://localhost:8000/chatbot"  # port-forward 환경
# API_BASE = "https://hanzanzu.cloud/api/python"  # 외부 도메인 (Istio rewrite)

def run_evaluation():
    results = []
    
    # 기존 결과 로드 (있으면)
    try:
        with open('evaluation_results.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
            print(f"📂 기존 결과 {len(results)}개 로드됨")
    except:
        pass
    
    for case in test_cases:
        # 이미 처리한 경우 스킵
        if any(r['id'] == case['id'] for r in results):
            print(f"⏭️  테스트 {case['id']} 이미 완료, 스킵")
            continue
            
        print(f"\n{'='*50}")
        print(f"테스트 {case['id']}: {case['question'][:30]}...")
        
        try:
            # API 호출
            endpoint = "/classic-chat" if case['category'] == 'classic' else "/chat"
            response = requests.post(
                f"{API_BASE}{endpoint}",
                json={"message": case['question']},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data['answer']
                drinks = data['drinks']
                
                # 키워드 체크
                keyword_hits = sum(1 for kw in case['expected_keywords'] if kw in answer)
                keyword_score = keyword_hits / len(case['expected_keywords']) * 100
                
                # 결과 저장
                result = {
                    "id": case['id'],
                    "category": case['category'],
                    "question": case['question'],
                    "answer": answer[:200] + "..." if len(answer) > 200 else answer,
                    "drinks_count": len(drinks),
                    "keyword_score": keyword_score,
                    "pass": keyword_score >= 50
                }
                results.append(result)
                
                print(f"✅ 키워드 점수: {keyword_score:.1f}%")
                print(f"🍶 추천 술: {[d['name'] for d in drinks[:3]]}")
            else:
                print(f"❌ API 오류: {response.status_code}")
                results.append({
                    "id": case['id'],
                    "category": case['category'],
                    "pass": False,
                    "error": response.status_code
                })
                
        except Exception as e:
            print(f"❌ 예외 발생: {e}")
            results.append({
                "id": case['id'],
                "category": case['category'],
                "pass": False,
                "error": str(e)
            })
        
        # 매 테스트마다 중간 저장
        with open('evaluation_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 최종 리포트
    print("\n" + "="*50)
    print("📊 RAG 평가 결과")
    print("="*50)
    
    passed = sum(1 for r in results if r.get('pass', False))
    total = len(results)
    accuracy = passed / total * 100
    
    print(f"통과: {passed}/{total} ({accuracy:.1f}%)")
    print("📁 결과 저장: evaluation_results.json")
    
    return results

if __name__ == "__main__":
    run_evaluation()
