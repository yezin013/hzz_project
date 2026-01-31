# RAG Evaluation

RAG 챗봇 정확도 평가를 위한 테스트 도구입니다.

## 파일 구조
- `golden_dataset.py`: 테스트 케이스 10개 (질문 + 예상 키워드)
- `run_evaluation.py`: 자동 평가 스크립트

## 사용법

```bash
cd backend/tests/rag_evaluation
python run_evaluation.py
```

## 평가 항목
| 카테고리 | 테스트 내용 |
|---------|------------|
| weather | 날씨 기반 추천 |
| abv | 도수 기반 추천 |
| food | 안주 기반 추천 |
| season | 계절 기반 추천 |
| mood | 기분 기반 추천 |
| recipe | 칵테일 레시피 |
| classic | 고전문학 (classic-chat) |
| region | 지역 기반 추천 |
| gift | 선물용 추천 |
| off-topic | 거절 테스트 |

## 평가 지표
- **키워드 점수**: 예상 키워드가 답변에 포함된 비율
- **통과 기준**: 키워드 점수 50% 이상
