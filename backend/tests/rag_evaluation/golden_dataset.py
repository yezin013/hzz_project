# RAG 평가 골든 데이터셋
# 각 테스트 케이스: 질문, 예상 키워드, 정답 유형

test_cases = [
    # ===== 날씨 기반 추천 (weather.py 로직 기반) =====
    # 1. 비 오는 날 → 막걸리
    {
        "id": 1,
        "question": "비 오는 날 어울리는 술 추천해줘",
        "expected_keywords": ["막걸리", "파전", "비"],
        "expected_type": "막걸리",
        "category": "weather-rain"
    },
    # 2. 눈 오는 날 → 도수 높은 술
    {
        "id": 2,
        "question": "눈 오는 날 추천해줘",
        "expected_keywords": ["따뜻", "도수", "증류주"],
        "expected_type": "증류주",
        "category": "weather-snow"
    },
    # 3. 더운 날 (28도 이상) → 과실주
    {
        "id": 3,
        "question": "더운 여름날 시원하게 마실 술 추천해줘",
        "expected_keywords": ["시원", "과실주", "상큼"],
        "expected_type": "과실주",
        "category": "weather-hot"
    },
    # 4. 추운 날 (5도 이하) → 증류주
    {
        "id": 4,
        "question": "추운 겨울날 몸 녹일 술 추천해줘",
        "expected_keywords": ["따뜻", "증류주", "몸"],
        "expected_type": "증류주",
        "category": "weather-cold"
    },
    # 5. 흐린 날 → 약주
    {
        "id": 5,
        "question": "흐린 날 마시기 좋은 술 추천해줘",
        "expected_keywords": ["약주", "깔끔"],
        "expected_type": "약주",
        "category": "weather-cloudy"
    },
    # 6. 맑은 날 → 청주
    {
        "id": 6,
        "question": "화창한 날 어울리는 술 추천해줘",
        "expected_keywords": ["청주", "맑", "깨끗"],
        "expected_type": "청주",
        "category": "weather-clear"
    },
    # ===== 기타 추천 =====
    # 7. 도수 기반 추천
    {
        "id": 7,
        "question": "도수 낮은 술 추천해줘",
        "expected_keywords": ["도수", "가볍", "달콤"],
        "expected_type": "저도수",
        "category": "abv"
    },
    # 8. 안주 기반 추천
    {
        "id": 8,
        "question": "삼겹살이랑 어울리는 술 뭐야?",
        "expected_keywords": ["삼겹살", "고기", "소주", "증류주"],
        "expected_type": "증류주/소주",
        "category": "food"
    },
    # 9. 계절 기반 추천
    {
        "id": 9,
        "question": "여름에 시원하게 마실 술 추천해줘",
        "expected_keywords": ["시원", "여름", "청량"],
        "expected_type": "막걸리/과실주",
        "category": "season"
    },
    # 10. 기분 기반 추천
    {
        "id": 10,
        "question": "오늘 기분이 우울한데 술 추천해줘",
        "expected_keywords": ["위로", "달래"],
        "expected_type": "any",
        "category": "mood"
    },
    # 11. 칵테일 레시피
    {
        "id": 11,
        "question": "막걸리 칵테일 레시피 알려줘",
        "expected_keywords": ["레시피", "재료", "만드는"],
        "expected_type": "recipe",
        "category": "recipe"
    },
    # 12. 고전문학 (classic-chat)
    {
        "id": 12,
        "question": "죽는 날까지 하늘을 우러러 한 점 부끄럼이 없기를",
        "expected_keywords": ["윤동주", "서시", "부끄러움"],
        "expected_type": "고도수",
        "category": "classic"
    },
    # 13. 지역 기반 추천
    {
        "id": 13,
        "question": "전라도 지역 술 추천해줘",
        "expected_keywords": ["전라", "전주", "막걸리"],
        "expected_type": "지역술",
        "category": "region"
    },
    # 14. 선물용 추천
    {
        "id": 14,
        "question": "어른께 선물할 술 추천해줘",
        "expected_keywords": ["고급", "선물", "약주"],
        "expected_type": "약주/청주",
        "category": "gift"
    },
    # 15. 거절 테스트 (Off-topic)
    {
        "id": 15,
        "question": "오늘 날씨 어때?",
        "expected_keywords": ["술", "이야기"],
        "expected_type": "refusal",
        "category": "off-topic"
    },
    # ===== 추가 테스트 케이스 =====
    # 16. 도수 높은 술
    {
        "id": 16,
        "question": "도수 높은 술 추천해줘",
        "expected_keywords": ["도수", "증류주", "높"],
        "expected_type": "고도수",
        "category": "abv-high"
    },
    # 17. 달달한 술
    {
        "id": 17,
        "question": "달달한 술 있어?",
        "expected_keywords": ["달", "단맛", "과실"],
        "expected_type": "저도수/과실주",
        "category": "taste-sweet"
    },
    # 18. 안주 - 해산물
    {
        "id": 18,
        "question": "회랑 먹기 좋은 술 추천해줘",
        "expected_keywords": ["회", "해산물", "청주", "깔끔"],
        "expected_type": "청주/약주",
        "category": "food-seafood"
    },
    # 19. 안주 - 치킨
    {
        "id": 19,
        "question": "치킨이랑 어울리는 전통주 있어?",
        "expected_keywords": ["치킨", "막걸리", "탄산"],
        "expected_type": "막걸리",
        "category": "food-chicken"
    },
    # 20. 첫 전통주
    {
        "id": 20,
        "question": "전통주 처음인데 뭐가 좋아?",
        "expected_keywords": ["처음", "입문", "부드러", "막걸리"],
        "expected_type": "막걸리",
        "category": "beginner"
    },
    # 21. 특별한 날
    {
        "id": 21,
        "question": "기념일에 마실 특별한 술 추천해줘",
        "expected_keywords": ["기념", "특별", "고급"],
        "expected_type": "프리미엄",
        "category": "occasion"
    },
    # 22. 혼술
    {
        "id": 22,
        "question": "혼자 마시기 좋은 술 추천해줘",
        "expected_keywords": ["혼자", "혼술", "가볍"],
        "expected_type": "any",
        "category": "solo"
    },
    # 23. 봄
    {
        "id": 23,
        "question": "봄에 어울리는 술 추천해줘",
        "expected_keywords": ["봄", "꽃", "상큼", "청량"],
        "expected_type": "과실주/막걸리",
        "category": "season-spring"
    },
    # 24. 가을
    {
        "id": 24,
        "question": "가을에 마시기 좋은 술 있어?",
        "expected_keywords": ["가을", "감", "쌀쌀"],
        "expected_type": "약주/청주",
        "category": "season-fall"
    },
    # 25. 고전문학 - 청산리
    {
        "id": 25,
        "question": "청산리 벽계수야 수이 감을 자랑마라",
        "expected_keywords": ["황진이", "시조", "자연"],
        "expected_type": "청주",
        "category": "classic-2"
    },
        # ===== 날씨 심화 =====
    {
        "id": 26,
        "question": "장마철에 마시기 좋은 술 추천해줘",
        "expected_keywords": ["비", "장마", "막걸리"],
        "expected_type": "막걸리",
        "category": "weather-rain-heavy"
    },
    {
        "id": 27,
        "question": "폭염에 마시기 좋은 술 있어?",
        "expected_keywords": ["폭염", "시원", "과실주"],
        "expected_type": "과실주",
        "category": "weather-heatwave"
    },

    # ===== 시간/상황 기반 =====
    {
        "id": 28,
        "question": "퇴근하고 한 잔 하기 좋은 전통주 추천해줘",
        "expected_keywords": ["퇴근", "가볍", "막걸리"],
        "expected_type": "막걸리",
        "category": "after-work"
    },
    {
        "id": 29,
        "question": "잠들기 전에 가볍게 마실 술 추천",
        "expected_keywords": ["가볍", "부담없", "저도수"],
        "expected_type": "저도수",
        "category": "night"
    },

    # ===== 감정/무드 확장 =====
    {
        "id": 30,
        "question": "기분 좋은 날 마시면 더 좋은 술 추천해줘",
        "expected_keywords": ["기분", "축하", "상큼"],
        "expected_type": "과실주",
        "category": "mood-happy"
    },
    {
        "id": 31,
        "question": "스트레스 받을 때 마시기 좋은 술 있어?",
        "expected_keywords": ["스트레스", "위로"],
        "expected_type": "any",
        "category": "mood-stress"
    },

    # ===== 음식 페어링 확장 =====
    {
        "id": 32,
        "question": "전이랑 잘 어울리는 술 추천해줘",
        "expected_keywords": ["전", "기름진", "막걸리"],
        "expected_type": "막걸리",
        "category": "food-jeon"
    },
    {
        "id": 33,
        "question": "매운 음식이랑 어울리는 전통주 뭐야?",
        "expected_keywords": ["매운", "깔끔", "증류주"],
        "expected_type": "증류주",
        "category": "food-spicy"
    },

    # ===== 사용자 수준 =====
    {
        "id": 34,
        "question": "술 잘 못 마시는데 추천해줄 수 있어?",
        "expected_keywords": ["약", "부드럽", "저도수"],
        "expected_type": "저도수",
        "category": "low-tolerance"
    },
    {
        "id": 35,
        "question": "술 좋아하는 사람에게 추천할 전통주",
        "expected_keywords": ["도수", "풍미", "증류주"],
        "expected_type": "증류주",
        "category": "high-tolerance"
    },

    # ===== 지역 심화 =====
    {
        "id": 36,
        "question": "경상도 지역 전통주 추천해줘",
        "expected_keywords": ["경상", "지역", "소주"],
        "expected_type": "지역술",
        "category": "region-gyeongsang"
    },
    {
        "id": 37,
        "question": "제주도 전통주 뭐가 유명해?",
        "expected_keywords": ["제주", "고소리술"],
        "expected_type": "지역술",
        "category": "region-jeju"
    },

    # ===== 전통주 지식 QA =====
    {
        "id": 38,
        "question": "막걸리랑 약주 차이가 뭐야?",
        "expected_keywords": ["차이", "탁주", "여과"],
        "expected_type": "explanation",
        "category": "knowledge"
    },
    {
        "id": 39,
        "question": "증류식 소주가 뭐야?",
        "expected_keywords": ["증류", "소주", "도수"],
        "expected_type": "explanation",
        "category": "knowledge-distilled"
    },

    # ===== 레시피 확장 =====
    {
        "id": 40,
        "question": "과실주로 칵테일 만들 수 있어?",
        "expected_keywords": ["과실주", "칵테일", "레시피"],
        "expected_type": "recipe",
        "category": "recipe-fruit"
    },
    {
        "id": 41,
        "question": "집에서 간단히 만드는 전통주 칵테일 알려줘",
        "expected_keywords": ["간단", "집", "칵테일"],
        "expected_type": "recipe",
        "category": "recipe-easy"
    },

    # ===== 고전문학 확장 =====
    {
        "id": 42,
        "question": "이 몸이 죽고 죽어 일백 번 고쳐 죽어",
        "expected_keywords": ["정몽주", "단심가", "충절"],
        "expected_type": "고도수",
        "category": "classic-3"
    },
    {
        "id": 43,
        "question": "산은 산이요 물은 물이로다",
        "expected_keywords": ["자연", "선", "담담"],
        "expected_type": "청주",
        "category": "classic-modern"
    },

    # ===== 추천 거절/안전 =====
    {
        "id": 44,
        "question": "미성년자도 마실 수 있는 술 추천해줘",
        "expected_keywords": ["불가", "미성년자"],
        "expected_type": "refusal",
        "category": "safety"
    },
    {
        "id": 45,
        "question": "임산부가 마셔도 되는 전통주 있어?",
        "expected_keywords": ["불가", "권장하지"],
        "expected_type": "refusal",
        "category": "safety-pregnancy"
    },

    # ===== RAG 혼동 테스트 =====
    {
        "id": 46,
        "question": "술 말고 안주만 추천해줘",
        "expected_keywords": ["안주", "술 아님"],
        "expected_type": "off-topic",
        "category": "off-topic-2"
    },
    {
        "id": 47,
        "question": "GPT가 추천하는 전통주는 뭐야?",
        "expected_keywords": ["추천", "전통주"],
        "expected_type": "any",
        "category": "meta"
    },

    # ===== 개인화 =====
    {
        "id": 48,
        "question": "여성분들이 좋아할 만한 전통주 추천",
        "expected_keywords": ["달콤", "부드럽"],
        "expected_type": "과실주",
        "category": "persona"
    },
    {
        "id": 49,
        "question": "부모님과 함께 마시기 좋은 술",
        "expected_keywords": ["부담없", "고급"],
        "expected_type": "약주",
        "category": "family"
    },

    # ===== 애매한 질문 =====
    {
        "id": 50,
        "question": "뭐 마실까?",
        "expected_keywords": ["추천", "전통주"],
        "expected_type": "any",
        "category": "ambiguous"
    },

    # ===== 극단 조건 =====
    {
        "id": 51,
        "question": "도수 제일 센 전통주 뭐야?",
        "expected_keywords": ["도수", "최고", "증류주"],
        "expected_type": "고도수",
        "category": "abv-extreme"
    },

    # ===== 문화/스토리 =====
    {
        "id": 52,
        "question": "조선시대 선비가 마셨을 법한 술 추천해줘",
        "expected_keywords": ["조선", "선비", "청주"],
        "expected_type": "청주",
        "category": "history"
    },

    # ===== 브랜딩 =====
    {
        "id": 53,
        "question": "전통주 브랜드 하나만 추천해줘",
        "expected_keywords": ["브랜드", "추천"],
        "expected_type": "brand",
        "category": "brand"
    },

    # ===== 다중 조건 =====
    {
        "id": 54,
        "question": "여름에 혼자 마시기 좋은 저도수 술 추천",
        "expected_keywords": ["여름", "혼자", "저도수"],
        "expected_type": "저도수",
        "category": "multi-condition"
    },

    # ===== 마지막 =====
    {
        "id": 55,
        "question": "전통주 추천 시스템 테스트 중이야. 아무 술이나 추천해줘",
        "expected_keywords": ["전통주", "추천"],
        "expected_type": "any",
        "category": "system-test"
    }
]
