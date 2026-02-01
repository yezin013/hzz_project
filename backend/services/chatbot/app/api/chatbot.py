from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import os
import random # Diversity logic
import json
import boto3
from app.utils.es_client import get_es_client
from app.utils.weather import fetch_owm_data
from app.utils.metrics import log_chatbot_metrics
import app.utils.secrets as secrets_util # Renamed to avoid confusion if needed, but let's just keep it clean
from app.utils.secrets import get_secrets
from pymongo import MongoClient
import pymysql
import urllib.parse

router = APIRouter()


# 💡 SonarQube High Severity 이슈 해결: 중복 리터럴을 상수로 대체

def get_mariadb_conn():
    return pymysql.connect(
        host=os.getenv("MARIADB_HOST", "192.168.0.182"),
        port=int(os.getenv("MARIADB_PORT", 3306)),
        user=os.getenv("MARIADB_USER", "root"),
        password=os.getenv("MARIADB_PASSWORD", ""),
        database=os.getenv("MARIADB_DB", "drink"),
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4'
    )


def detect_emotion_keywords(text: str) -> dict:
    """
    텍스트에서 감정 키워드를 감지하여 추천할 술의 특성 결정.
    Returns: {"type": "heavy" | "light", "emotions": [...]}
    """
    heavy_keywords = [
        "슬", "고독", "허무", "무상", "철학", "원망", "비극", "절망",
        "저항", "그리움", "이별", "죽음", "부끄러움", "한"
    ]
    light_keywords = [
        "밝", "설렘", "기쁨", "사랑", "즐거", "청춘", "봄", "꽃"
    ]
    
    detected_emotions = []
    for keyword in heavy_keywords:
        if keyword in text:
            detected_emotions.append(keyword)
    
    # 무거운 감정이 하나라도 있으면 고도수 추천
    if detected_emotions:
        return {"type": "heavy", "emotions": detected_emotions}
    
    # 가벼운 감정 체크
    for keyword in light_keywords:
        if keyword in text:
            return {"type": "light", "emotions": [keyword]}
    
    # 감정 감지 안 됨
    return {"type": "neutral", "emotions": []}

def prioritize_by_abv(drinks: list, emotion_type: str) -> list:
    """
    감정 타입에 따라 도수 기준으로 술 정렬.
    heavy: 고도수 우선 (내림차순)
    light: 저도수 우선 (오름차순)
    neutral: 원본 순서 유지
    """
    if emotion_type == "heavy":
        # 고도수 우선 (15도 이상을 앞으로)
        return sorted(drinks, key=lambda d: float(d.get('abv', 0)), reverse=True)
    elif emotion_type == "light":
        # 저도수 우선
        return sorted(drinks, key=lambda d: float(d.get('abv', 0)))
    else:
        # 원본 유지
        return drinks

def reorder_by_ai_mentions(answer: str, drinks: list) -> list:
    """
    AI 응답에서 언급된 술을 최상단으로 이동.
    Phase 1: AI-카드 불일치 해결.
    """
    mentioned = []
    remaining = []
    
    for drink in drinks:
        if drink['name'] in answer:
            mentioned.append(drink)
        else:
            remaining.append(drink)
    
    # 언급된 술 + 나머지
    return mentioned + remaining
REFUSAL_TOKEN = "[[REFUSAL]]"

class ChatRequest(BaseModel):
    message: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class ChatResponse(BaseModel):
    answer: str
    drinks: List[dict]

def search_liquor_for_rag(text: str, filters: dict = None):
    es = get_es_client()
    if not es:
        print("❌ Elasticsearch client not available")
        return []

    index_name = "liquor_integrated"

    # 기본 bool 쿼리 구조
    bool_query = {
        "should": [
            { "match": { "name": { "query": text, "boost": 3.0 } } },
            { "match": { "intro": { "query": text, "boost": 1.5 } } },
            { "match": { "description": { "query": text, "boost": 1.0 } } },
            { "match": { "foods": { "query": text, "boost": 2.0 } } }, 
        ],
        "minimum_should_match": 1,
        "filter": [] # 필터 조건 추가
    }

    # 스마트 필터 적용
    if filters:
        # 도수(ABV) 필터
        if 'min_abv' in filters or 'max_abv' in filters:
            range_query = {"range": {"alcohol": {}}}
            if 'min_abv' in filters:
                # DB는 0.0~1.0 단위일 수 있으므로 확인 필요 (현재 15% -> 0.15로 저장된 것으로 추정되나, 
                # 이전 코드에서 abv_raw * 100 하는거 보면 DB엔 0.15로 저장됨. 따라서 /100 해야함)
                # 안전하게 입력이 정수(15)면 0.15로 변환
                val = filters['min_abv']
                if val > 1: val = val / 100.0
                range_query["range"]["alcohol"]["gte"] = val
            
            if 'max_abv' in filters:
                val = filters['max_abv']
                if val > 1: val = val / 100.0
                range_query["range"]["alcohol"]["lte"] = val
            
            bool_query["filter"].append(range_query)
            print(f"🔍 Applied ABV Filter: {range_query}")

    query = {
        "query": { "bool": bool_query },
        "size": 20 
    }

    try:
        response = es.search(index=index_name, body=query)
        hits = response['hits']['hits']
        print(f"🔍 ES Search: Found {len(hits)} drinks for '{text}' with filters {filters}")

        results = []
        for hit in hits:
            source = hit['_source']

            # Alcohol formatting
            abv_raw = source.get('alcohol', 0)
            abv = f"{abv_raw * 100:.1f}".rstrip('0').rstrip('.') if abv_raw else "0"

            results.append({
                "id": source.get('drink_id'),
                "name": source.get('name'),
                "image_url": source.get('image_url'),
                "description": source.get('intro') or source.get('description', '')[:100],
                "abv": abv,
                "volume": source.get('volume'),
                "foods": source.get('foods', []),
                "full_desc": source.get('description', '')
            })
        return results
    except Exception as e:
        print(f"❌ ES Search error: {e}")
        return []

def invoke_nova(system_prompt: str, user_message: str):
    try:
        # AWS Bedrock Client
        # AWS Bedrock Client (Use IAM Role)
        bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name="us-east-1"
        )

        model_id = "amazon.nova-lite-v1:0"

        # Nova 모델 요청 바디 구성
        body = {
            "system": [{"text": system_prompt}],
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": user_message}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 1000,
                "temperature": 0.7,
                "topP": 0.9
            }
        }

        # Measure Latency
        import time
        start_time = time.time()

        try:
            response = bedrock.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                guardrailIdentifier="6lsrxzd5pnlq",
                guardrailVersion="DRAFT"
            )
        except Exception as e:
            # 가드레일에 걸리면 예외가 발생할 수 있음 (또는 응답에 포함)
            print(f"⚠️ Guardrail or Bedrock Error: {e}")
            # 상수 토큰을 포함하여 반환하도록 수정
            return f"{REFUSAL_TOKEN} 그 이야기는 내 잘 모르겠고, 술 이야기나 합시다! 허허."

        end_time = time.time()
        latency = end_time - start_time

        response_body = json.loads(response.get('body').read())

        # Token Usage Logging
        usage = response_body.get('usage', {})
        input_tokens = usage.get('inputTokens', 0)
        output_tokens = usage.get('outputTokens', 0)
        total_tokens = usage.get('totalTokens', 0)
        print(f"💰 Bedrock Nova Token Usage: Input={input_tokens}, Output={output_tokens}, Total={total_tokens}")
        print(f"⏱️ Bedrock Latency: {latency:.4f}s")

        # 📊 Log metrics to Redis
        log_chatbot_metrics(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_seconds=latency,
            model=model_id,
            success=True,
            endpoint="chat"
        )

        # Guardrail에 의해 차단되었는지 확인 (amazon-bedrock-guardrailAction 필드 등 확인 필요하지만 심플하게 텍스트로 판단)
        output_text = response_body['output']['message']['content'][0]['text']

        return output_text

    except Exception as e:
        print(f"❌ Bedrock Nova Error: {e}")
        # 상수 토큰을 포함하여 반환하도록 수정
        return f"{REFUSAL_TOKEN} 아이고, 머리가 아파서 잠시 생각을 못하겠구만유. 다시 물어봐주시오."

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, req: Request):
    """챗봇 API - Rate Limited: 3회/분"""
    # Rate Limiting은 main.py의 global limiter 사용
    # (잘못된 inline 코드 제거)
    
    # 0. 스마트 필터 결정 (Smart Filtering Rules)
    smart_filters = {}
    weather_context = ""
    user_message_context = ""  # 사용자에게 보이는 멘트 (요일/시간 기반)
    current_temp = None

    # 0.1 날씨 기반 필터링 (키워드가 있을 때만 수행)
    weather_keywords = ["날씨", "비", "눈", "기온", "춥", "덥", "따뜻", "시원", "추워", "더워", "계절", "여름", "겨울", "가을", "봄", "오늘"]
    # 사용자 질문에 날씨 관련 단어가 포함되어 있거나, 위치 정보가 명시적으로 왔을 때만 날씨 API 호출
    should_check_weather = (request.latitude and request.longitude) and \
                           any(k in request.message for k in weather_keywords)

    if should_check_weather:
        try:
            w_data = await fetch_owm_data((request.latitude, request.longitude))
            if w_data:
                desc = w_data['weather'][0]['description']
                current_temp = w_data['main']['temp']
                weather_context = f"현재 위치 날씨: {desc}, 기온: {current_temp}도"
                print(f"🌦️ Chatbot Weather: {weather_context}")

                # 🌡️ 온도 기반 필터링 (3단계 세분화)
                if current_temp <= 5:  # 추움
                    if current_temp < -5:
                        # 극한추위: 영하 5도 이하 → 증류주급
                        smart_filters['min_abv'] = 25
                        print("🥶 극한추위 → 25% 이상 (증류주)")
                    elif current_temp < 0:
                        # 추움: 영하 0~5도 → 고도약주
                        smart_filters['min_abv'] = 18
                        print("❄️ 추움 → 18% 이상 (고도약주)")
                    else:
                        # 쌀쌀함: 0~5도 → 일반 약주
                        smart_filters['min_abv'] = 15
                        print("🌨️ 쌀쌀함 → 15% 이상 (약주)")
                    
                    weather_context += " (추운 날씨라 도수 높은 술을 우선 검색함)"
                
                elif current_temp >= 28:  # 더움 → 저도수/청량
                    smart_filters['max_abv'] = 10
                    weather_context += " (더운 날씨라 가벼운 술을 우선 검색함)"
                    print("🔥 더움 → 10% 이하 (청량)")
                
                # ☔ 날씨 상태 기반 필터링 (비/눈)
                if "비" in desc or "rain" in desc.lower():
                    # 비 오는 날 → 탁주(막걸리) 우선
                    weather_context += " (비 오는 날)"
                    print("☔ 비 → 탁주 우선")
                elif "눈" in desc or "snow" in desc.lower():
                    # 눈 오는 날 → 따뜻한 술 (청주/약주)
                    weather_context += " (눈 오는 날)"
                    print("❄️ 눈 → 따뜻한 술")
        except Exception as e:
            print(f"⚠️ Weather fetch failed: {e}")

    # 0.1.5 요일/시간 기반 사용자 멘트 생성 + 도수 필터링
    from datetime import datetime
    now = datetime.now()
    current_hour = now.hour
    day_of_week = now.weekday()  # 0=월요일, 4=금요일, 6=일요일
    
    # --- 시간대별 도수 필터링 ---
    time_abv_filter = {}
    if 22 <= current_hour or current_hour < 2:
        # 늦은 밤 (22시~익일 2시) → 고도수 (증류주급)
        user_message_context = "늦은 밤이니 진한 술로 하루를 마무리하시오"
        time_abv_filter['min_abv'] = 15
        print("🌙 밤 → 고도수(15%↑) 필터 적용")
    elif 12 <= current_hour < 17:
        # 낮 시간 (12시~17시) → 저도수 (막걸리급)
        user_message_context = "낮술은 가볍게 하시오"
        time_abv_filter['max_abv'] = 10
        print("☀️ 낮 → 저도수(10%↓) 필터 적용")
    elif 18 <= current_hour < 22:
        # 저녁 시간 → 제한 없음
        user_message_context = "저녁이니 마음껏 즐겨보시오"
    
    # --- 요일별 도수 필터링 ---
    day_names = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    if day_of_week == 4:  # 금요일 → 제한 없음
        user_message_context = f"금요일이니 한 주 수고하셨소! {user_message_context if user_message_context else '이 술로 마무리하시오~'}"
        print("🎉 금요일 → 도수 제한 없음")
    elif day_of_week == 5:  # 토요일 → 제한 없음
        user_message_context = f"토요일이니 마음껏 즐기시오! {user_message_context if user_message_context else ''}"
        print("🎊 토요일 → 도수 제한 없음")
    elif day_of_week == 6:  # 일요일 → 저도수 (내일 출근)
        user_message_context = f"일요일이구만, {user_message_context if user_message_context else '내일 출근 생각해서 적당히 하시오'}"
        if 'min_abv' in time_abv_filter:
            del time_abv_filter['min_abv']  # 밤이어도 일요일은 고도수 제외
        time_abv_filter['max_abv'] = 12  # 일요일은 저도수
        print("📅 일요일 → 저도수(12%↓) 필터 적용 (내일 출근)")
    elif day_of_week == 0:  # 월요일
        user_message_context = f"월요일의 피로를 이 술로 풀어보시오"
    else:
        # 다른 요일은 시간대 멘트만 사용
        if not user_message_context:
            user_message_context = f"{day_names[day_of_week]}이니 한 잔 어떠시오?"
    
    # 시간/요일 필터를 smart_filters에 병합 (날씨 필터와 중복 시 더 보수적으로)
    for key, val in time_abv_filter.items():
        if key == 'max_abv':
            # 기존 max_abv가 있으면 더 낮은 값 사용
            smart_filters['max_abv'] = min(smart_filters.get('max_abv', 100), val)
        elif key == 'min_abv':
            # 기존 min_abv가 있으면 더 높은 값 사용
            smart_filters['min_abv'] = max(smart_filters.get('min_abv', 0), val)
    
    print(f"💬 User Message Context: {user_message_context}")
    print(f"📊 Time/Day ABV Filters Applied: {time_abv_filter}")

    # 0.2 사용자 의도 기반 필터링 (키워드 오버라이드)
    # 날씨 필터보다 사용자가 직접 말한 조건이 우선순위가 높음
    # "독한거", "센거" -> min_abv 20
    if any(k in request.message for k in ["독한", "센 술", "도수 높은", "강한"]):
        smart_filters['min_abv'] = max(smart_filters.get('min_abv', 0), 20)
    
    # "가벼운", "음료수", "안 취하는" -> max_abv 7
    if any(k in request.message for k in ["가벼운", "약한", "음료", "순한"]):
        smart_filters['max_abv'] = 7
        if 'min_abv' in smart_filters: del smart_filters['min_abv'] # 상충되면 max 우선

    print(f"🧠 Smart Filters Determined: {smart_filters}")

    # 1. ES에서 관련 술 검색 (필터 적용)
    drinks = search_liquor_for_rag(request.message, filters=smart_filters)
    
    # 🎲 Diversity: 검색 결과 랜덤 샘플링 (다양성 확보)
    if len(drinks) > 10:
        # 상위 20개 중 랜덤 10개 선택
        drinks_sample = random.sample(drinks[:20], min(10, len(drinks[:20])))
        print(f"🎲 Randomized from top 20: {len(drinks_sample)} drinks selected for diversity")
        drinks = drinks_sample
    
    # 검색 결과가 너무 적으면(0개), 필터를 완화해서 재검색 (Fallback)
    if not drinks and smart_filters:
        print("⚠️ No drinks found with filters, retrying without filters...")
        drinks = search_liquor_for_rag(request.message)

    # 검색 결과를 프롬프트에 주입할 텍스트로 변환
    context_text = ""
    if drinks:
        for i, drink in enumerate(drinks[:5]):  # 상위 5개만 컨텍스트에 포함
            context_text += f"{i+1}. 이름: {drink['name']} (도수: {drink.get('abv', '?')}%, 증류소: {drink.get('brewery_name', '정보없음')})\n"
            context_text += f"   특징: {drink.get('intro', '설명 없음')}\n"
            context_text += f"   맛/향: {drink.get('taste_summary', '')}\n\n"
    else:
        context_text = "검색된 술이 없습니다. 사용자의 질문에 맞춰 일반적인 전통주 지식으로 답변하세요."

    system_prompt = f"""
너는 한국의 전통 주막을 지키는 '주모'다.
사용자에게 구수하고 친근한 사극체 말투(예: "어서오시오!", "이 술은 참말로 기가 막히지!", "한 잔 받으시오~")를 사용하여 대화하라.

[핵심 역할]
1. 사용자의 기분, 날씨, 상황에 맞는 전통주를 [술 목록]에서 골라 추천한다.
2. 술을 추천할 때는 그 술의 이름, 맛, 특징을 맛깔나게 설명한다.
3. 목록에 없는 술은 절대 추천하지 않는다.

[답변 가이드]
1. **날씨 정보 활용 (매우 중요)**:
   - [현재 날씨 정보]가 제공되었다면, **반드시 현재 기온과 날씨 상태를 구체적으로 언급**하라.
   - 예: "지금 서울은 영하 2도로 쌀쌀하구만유. 이런 날엔 따뜻한 청주가 제격이지요."
   - 날씨에 따라 추천 이유를 설명하라 (비 → 파전/막걸리, 추위 → 고도수/따뜻한 술 등).

2. **추천 개수**:
   - 사용자가 **특별히 개수를 지정하지 않으면 기본적으로 1개만** 추천하라.
   - 사용자가 "3개 추천해줘"처럼 숫자를 언급하면 그에 맞춰 추천하라.

3. 일반적인 요청:
   - "오늘 같은 날엔 이 술이 딱이오!"라며 자연스럽게 권한다.

4. 칵테일 레시피 요청:
   - [술 목록]의 정보나 너의 지식을 활용하여 전통주 칵테일 레시피를 알려준다.
   - **반드시 아래 JSON 형식을 답변의 마지막에 포함하라. (마크다운 코드블럭 없이 raw JSON으로)**:
     
     {{
       "cocktail": {{
         "name": "칵테일 이름",
         "base_liquor": "베이스가 되는 술 이름",
         "ingredients": ["재료1", "재료2", ...],
         "instructions": ["1. 첫번째 단계", "2. 두번째 단계", "3. 마무리"]
       }}
     }}

   - 설명 텍스트를 먼저 쓰고, 이 JSON을 맨 마지막에 붙여라. 이 JSON은 UI 카드 생성용이다.

[제약 사항]
- [술 목록]에 적절한 술이 없거나 사용자가 엉뚱한 소리를 하면 반드시 답변에 "{REFUSAL_TOKEN}"을 포함하라.
- 답변은 줄글로 자연스럽게 작성하되, 가독성을 위해 적절히 줄바꿈을 하라.
- **중요: 모든 답변과 JSON 데이터의 값(Value)은 반드시 '한국어(Korean)'로만 작성하라.**
- **중요: 유니코드 이스케이프 시퀀스(\\uXXXX)나 러시아어(키릴 문자) 등 외국어를 절대 사용하지 말라.**

[현재 날씨 정보]
{weather_context if weather_context else "정보 없음 (일반적인 추천 진행)"}

[특별 멘트]
{user_message_context if user_message_context else ""}
(답변에 이 멘트를 자연스럽게 포함하여 사용자와 대화하라. 예: "어서오시오! {user_message_context}!")

[술 목록]
{context_text}
"""

    # 3. Nova 호출
    answer = invoke_nova(system_prompt, request.message)

    # 4. 답변 분석 및 필터링
    # REFUSAL_TOKEN 토큰이 있으면 술 정보(drinks)를 비우고, 토큰은 사용자에게 보이지 않게 제거함
    if REFUSAL_TOKEN in answer:
        drinks = []
        answer = answer.replace(REFUSAL_TOKEN, "").strip()
        print("🚫 Refusal detected. Cleared drinks list.")
    else:
        # AI가 답변에서 언급한 술만 필터링하여 카드 제공
        # 1. 언급된 순서대로 정렬
        reordered = reorder_by_ai_mentions(answer, drinks)
        
        # 2. 실제로 언급된 술 개수 카운트
        mentioned_count = 0
        for d in drinks:
            if d['name'] in answer:
                mentioned_count += 1
        
        # 3. 언급된 술이 있으면 그만큼만 반환, 없으면 기본 1개 반환
        if mentioned_count > 0:
            drinks = reordered[:mentioned_count]
        else:
             # AI가 추천은 했는데 정확한 이름을 언급 안했거나 매칭 실패 시 -> 가장 적절한 1개(reordered[0])는 제공
             # 하지만 reordered는 언급 안되면 원래 순서대로임.
             # 이 경우 그냥 첫번째 술을 보여주는게 안전함.
            drinks = drinks[:1]

    return {
        "answer": answer,
        "drinks": drinks
    }

@router.post("/classic-chat", response_model=ChatResponse)
async def classic_chat(request: ChatRequest):
    """
    고전문학 문구에 맞는 전통주를 추천하는 전용 챗봇.
    기본 구조(ES 검색 + Nova 호출)는 기존 /chat 과 같고,
    system_prompt만 고전문학/분위기 설명에 맞게 바꾼 버전.
    """
    # 1. ES에서 관련 술 검색 (그대로 재사용)
    all_drinks = search_liquor_for_rag(request.message)

    # 1.5 감정 키워드 감지
    emotion_data = detect_emotion_keywords(request.message)
    print(f"🎭 Detected Emotion: {emotion_data['type']} - {emotion_data['emotions']}")

    # 1.6 감정에 따라 도수 기준 정렬
    all_drinks = prioritize_by_abv(all_drinks, emotion_data['type'])

    # Diversity Logic (정렬 후 샘플링)
    if len(all_drinks) > 6:
        drinks = random.sample(all_drinks[:12], 6)  # 상위 12개 중 6개 랜덤
    else:
        drinks = all_drinks
    # 2. 컨텍스트 텍스트 구성
    if drinks:
        context_text = "다음은 자네가 추천할 수 있는 우리 술 목록일세:\n"
        for i, d in enumerate(drinks):
            context_text += f"{i+1}. {d['name']} (도수: {d['abv']}%, 용량: {d['volume']})\n"
            context_text += f"   특징: {d['description']}\n"
            context_text += f"   어울리는 안주: {', '.join(d['foods'])}\n\n"
    else:
        context_text = "관련된 술 정보를 찾지 못했네. 일반적인 지식으로 대답하게."

    # 3. 고전문학 전용 시스템 프롬프트
    system_prompt = f"""
너는 '주모'라는 캐릭터다.
한국의 전통 주막 주인의 말투를 사용하며 구수하고 친근한 사극체로만 대답하라.
예: "허허, 어서오시오.", "이 술은 참말로 기가 막히지요.", "한 잔 들이키고 마음을 풀어보시오~"

사용자가 보내는 문장은 한국 고전문학(시조, 한시, 고전 소설, 시, 명문장)의 한 구절 또는 작품이다.

답변은 반드시 아래 순서로 자연스러운 문장으로 작성하되, JSON 형식이나 딱딱한 구조는 절대 사용하지 말아라:

1) 먼저 사용자가 보낸 구절을 주모 말투로 다시 읊어준다.
   예: "허허, 그대가 읊은 말은 이러하오: '산은 옛 산이로되...'"

2) 작가의 삶과 시대상을 분석한다:
   - 작가가 살았던 시대의 역사적 배경, 사회적 상황을 간략히 설명한다.
   - 작가의 생애, 경험, 처지가 작품에 어떻게 반영되었는지 언급한다.
   - 작가가 살았던 지역의 특색이나 관련 정서가 있다면 짧게 언급한다.
   예: "윤동주는 일제강점기 암흑기에, 북간도 용정에서 나고 자랐소. 그 시절 젊은이들의 절망과 저항 정신이..."

3) 구절의 의미를 현대어로 풀이하되, 문학적으로 깊이 있게 설명한다.
   원문의 상징, 비유, 철학적 의미를 2~3문장으로 간결하게 해석한다.

4) 구절 속 감정, 분위기, 계절감, 숨겨진 정서를 짧게 분석한다.

5) [술 목록]에서 1~2개만 골라 추천한다.
   목록에 없는 술은 절대 지어내지 말고, 반드시 목록에 있는 것만 언급한다.

6) 왜 이 술이 그 구절의 분위기에 어울리는지 설명한다.
   - 시대상이나 작가의 삶과 술의 연결고리 (예: "그 시절 북방의 추위를 녹이던 증류주...")
   - 구절 속 이미지나 감정과 술의 특성을 연결지어 설명한다.

---------------------------------------------------------
[감정-술 매칭 절대 규칙]

이 규칙은 최우선이며, 절대 어겨서는 안 된다:

1) 슬픔, 허무, 무상함, 철학적 성찰, 저항, 고독 → **도수 높은 증류주, 묵직한 약주, 숙성주**
   달콤한 술, 스파클링, 가벼운 막걸리는 절대 금지.

2) 고요함, 달빛, 잔잔함, 여운, 그리움 → **청주·약주 계열**

3) 밝음, 설렘, 따뜻함, 기쁨, 사랑 → **과실주·라이트 막걸리, 화사한 술**

4) 분노·비극·원망·절절함 → **씁쓸한 뒷맛의 고도수 술**

5) 철학적 문장(인생·명언류), 효심, 헌신 → **묵직한 숙성 약주 / 고도수 증류주**

---------------------------------------------------------
[중요 규칙]

- 답변은 자연스러운 사극체 문장으로만 작성한다. JSON이나 구조화된 형식은 절대 사용하지 말아라.
- 작품명·작가명을 모르면 "작품명은 알 수 없으나..." 또는 "이 구절은 어느 선비의 글인지 모르겠으나..."라고 솔직히 말한다.
- 설명은 간결하게. 불필요하게 길게 쓰지 말아라.
- 술 이름만 언급하고, id나 기술적 정보는 언급하지 말아라.
- 반드시 사극체 말투를 유지한다.

---------------------------------------------------------

[술 목록]
{context_text}
"""

    # 4. Nova 호출
    answer = invoke_nova(system_prompt, request.message)

    # 5. AI가 언급한 술을 카드 최상단으로 이동 (Phase 1)
    drinks = reorder_by_ai_mentions(answer, drinks)
    print(f"🍶 Reordered Drinks: {[d['name'] for d in drinks[:3]]}")

    # 6. REFUSAL 처리 로직은 기존과 동일하게 재사용
    # REFUSAL_TOKEN 토큰이 있으면 술 정보(drinks)를 비우고, 토큰은 사용자에게 보이지 않게 제거함
    if REFUSAL_TOKEN in answer:
        drinks = []
        answer = answer.replace(REFUSAL_TOKEN, "").strip()

    return {
        "answer": answer,
        "drinks": drinks[:3]
    }

@router.get("/debug/mongo/shops")
async def debug_mongo_shops(name: str = "감홍로", collection: str = None):
    """
    Debug endpoint to inspect MongoDB data directly.
    """
    try:
        secrets = get_secrets()
        mongo_url = secrets.get('MONGO_URL')
        
        if not mongo_url:
            user = secrets.get('MONGO_USERNAME', 'root')
            password = secrets.get('MONGO_PASSWORD', '')
            host = secrets.get('MONGO_HOST', 'localhost')
            port = secrets.get('MONGO_PORT', '27017')
            auth_db = "admin"
            
            if password:
                encoded_password = urllib.parse.quote_plus(password)
                mongo_url = f"mongodb://{user}:{encoded_password}@{host}:{port}/{auth_db}"
        
        if not mongo_url:
             return {"error": "Could not construct Mongo URL"}

        client = MongoClient(mongo_url, serverSelectionTimeoutMS=3000)
        db = client["liquor"]
        
        cols = db.list_collection_names()
        
        # Decide collection
        if collection and collection in cols:
            target_col = collection
        else:
            # Default priority logic
            target_col = "products" if "products" in cols else ("crawling_results" if "crawling_results" in cols else cols[0])
        
        doc = db[target_col].find_one({"name": {"$regex": name}})
        
        if doc:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
            return {
                "status": "Found",
                "collection": target_col,
                "data": doc
            }
        else:
            return {
                "status": "Not Found",
                "collection": target_col,
                "collections_available": cols
            }

    except Exception as e:
        return {"error": str(e)}

@router.get("/debug/mariadb/schema")
async def debug_mariadb_schema(table: str = "menu_shop"):
    try:
        conn = get_mariadb_conn()
        with conn.cursor() as cursor:
            # 💡 SonarQube Security Fix: Validate table name against a whitelist to prevent SQL Injection
            allowed_tables = ["menu_shop", "region", "drink_info", "drink_region", "cocktail_info", "fair_info"]
            if table not in allowed_tables:
                return {"error": f"Access denied for table '{table}'. Allowed tables: {', '.join(allowed_tables)}"}
            
            cursor.execute(f"SELECT * FROM {table} LIMIT 1")
            row = cursor.fetchone()
            return {"table": table, "columns": list(row.keys()) if row else "Empty Table"}
    except Exception as e:
        return {"error": str(e)}

@router.get("/debug/mariadb/provinces")
async def debug_mariadb_provinces():
    """List distinct provinces from MariaDB region table."""
    try:
        conn = get_mariadb_conn()
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT province FROM region ORDER BY province")
            rows = cursor.fetchall()
            return {"provinces": [row['province'] for row in rows]}
    except Exception as e:
        return {"error": str(e)}

@router.get("/debug/mariadb/cities_by_province")
async def debug_cities_by_province():
    """List cities grouped by province from MariaDB region table."""
    try:
        conn = get_mariadb_conn()
        with conn.cursor() as cursor:
            cursor.execute("SELECT province, city FROM region ORDER BY province, city")
            rows = cursor.fetchall()
            result = {}
            for row in rows:
                prov = row['province']
                city = row['city']
                if prov not in result:
                    result[prov] = []
                result[prov].append(city)
            return {"data": result, "total": len(rows)}
    except Exception as e:
        return {"error": str(e)}

@router.get("/debug/mariadb/drink_region_check/{province}")
async def debug_drink_region_check(province: str):
    """Check drink_region linkage for a specific province."""
    try:
        conn = get_mariadb_conn()
        with conn.cursor() as cursor:
            # 1. Check how many drinks have this province in region table
            sql1 = """
                SELECT COUNT(DISTINCT d.drink_id) as linked_count
                FROM drink_info d
                JOIN drink_region dr ON d.drink_id = dr.drink_id
                JOIN region r ON dr.region_id = r.id
                WHERE r.province = %s
            """
            cursor.execute(sql1, (province,))
            linked = cursor.fetchone()
            
            # 2. Get sample drinks
            sql2 = """
                SELECT d.drink_id, d.drink_name, r.province, r.city
                FROM drink_info d
                JOIN drink_region dr ON d.drink_id = dr.drink_id
                JOIN region r ON dr.region_id = r.id
                WHERE r.province = %s
                LIMIT 10
            """
            cursor.execute(sql2, (province,))
            samples = cursor.fetchall()
            
            # 3. Check region table for this province
            sql3 = "SELECT id, province, city FROM region WHERE province = %s LIMIT 10"
            cursor.execute(sql3, (province,))
            regions = cursor.fetchall()
            
            return {
                "province": province,
                "linked_drink_count": linked['linked_count'] if linked else 0,
                "sample_drinks": [{"id": s['drink_id'], "name": s['drink_name'], "city": s['city']} for s in samples],
                "region_entries": [{"id": r['id'], "province": r['province'], "city": r['city']} for r in regions]
            }
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}

@router.get("/debug/mariadb/drinks_per_province")
async def debug_drinks_per_province():
    """Count drinks per province from MariaDB."""
    try:
        conn = get_mariadb_conn()
        with conn.cursor() as cursor:
            sql = """
                SELECT r.province, COUNT(DISTINCT d.drink_id) as drink_count
                FROM drink_info d
                LEFT JOIN drink_region dr ON d.drink_id = dr.drink_id
                LEFT JOIN region r ON dr.region_id = r.id
                GROUP BY r.province
                ORDER BY drink_count DESC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            return {"counts": [{"province": row['province'], "count": row['drink_count']} for row in rows]}
    except Exception as e:
        return {"error": str(e)}

@router.get("/debug/es/raw/{drink_id}")
async def debug_es_raw_document(drink_id: int):
    """Get raw ES document for a specific drink_id."""
    try:
        es = get_es_client()
        if not es:
            return {"error": "ES Connection Failed"}
        
        search_res = es.search(index="liquor_integrated", body={
            "query": {"term": {"drink_id": drink_id}},
            "size": 1
        })
        
        if search_res['hits']['hits']:
            doc = search_res['hits']['hits'][0]
            return {
                "es_id": doc['_id'],
                "drink_id": doc['_source'].get('drink_id'),
                "name": doc['_source'].get('name'),
                "region": doc['_source'].get('region'),
                "lowest_price": doc['_source'].get('lowest_price'),
                "selling_shops": doc['_source'].get('selling_shops'),
                "all_fields": list(doc['_source'].keys())
            }
        else:
            return {"error": "Not found in ES", "drink_id": drink_id}
    except Exception as e:
        return {"error": str(e)}

@router.post("/debug/es/refresh")
async def refresh_es_index():
    """Force refresh ES index to make updates searchable immediately."""
    try:
        es = get_es_client()
        if not es:
            return {"error": "ES Connection Failed"}
        
        result = es.indices.refresh(index="liquor_integrated")
        return {"status": "Index refreshed", "result": str(result)}
    except Exception as e:
        return {"error": str(e)}

@router.get("/debug/es/query_region/{province}")
async def debug_es_query_region(province: str):
    """Debug ES query for a specific province."""
    try:
        es = get_es_client()
        if not es:
            return {"error": "ES Connection Failed"}
        
        # Try different query types
        queries = {
            "match": {"query": {"match": {"region.province": province}}, "size": 3},
            "term": {"query": {"term": {"region.province": province}}, "size": 3},
            "term_keyword": {"query": {"term": {"region.province.keyword": province}}, "size": 3},
        }
        
        results = {}
        for qname, qbody in queries.items():
            try:
                res = es.search(index="liquor_integrated", body=qbody)
                hits = res['hits']['hits']
                results[qname] = {
                    "count": len(hits),
                    "samples": [h['_source'].get('name') for h in hits]
                }
            except Exception as e:
                results[qname] = {"error": str(e)}
        
        return {"province": province, "query_results": results}
    except Exception as e:
        return {"error": str(e)}

@router.get("/debug/es/search_raw_by_name/{name}")
async def debug_es_search_raw_by_name(name: str):
    """Get raw ES document searching by name."""
    try:
        es = get_es_client()
        if not es:
            return {"error": "ES Connection Failed"}
        
        search_res = es.search(index="liquor_integrated", body={
            "query": {"match": {"name": name}},
            "size": 1
        })
        
        if search_res['hits']['hits']:
            doc = search_res['hits']['hits'][0]
            return {
                "es_id": doc['_id'],
                "drink_id": doc['_source'].get('drink_id'),
                "name": doc['_source'].get('name'),
                "region": doc['_source'].get('region'),
                "lowest_price": doc['_source'].get('lowest_price'),
                "selling_shops": doc['_source'].get('selling_shops'),
                "score": doc['_score']
            }
        else:
            return {"error": "Not found in ES", "name": name}
    except Exception as e:
        return {"error": str(e)}

@router.post("/debug/sync/region/all")
async def bulk_sync_region():
    """
    Bulk sync region data (province, city) from MariaDB to Elasticsearch.
    Updates only the region field without touching other data.
    """
    try:
        # 1. Connect to MariaDB
        conn = get_mariadb_conn()
        
        # 2. Fetch all drink_id -> region mappings
        region_map = {}
        with conn.cursor() as cursor:
            sql = """
                SELECT d.drink_id, d.drink_name, r.province, r.city
                FROM drink_info d
                LEFT JOIN drink_region dr ON d.drink_id = dr.drink_id
                LEFT JOIN region r ON dr.region_id = r.id
                WHERE r.province IS NOT NULL
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            for row in rows:
                region_map[row['drink_id']] = {
                    "drink_name": row['drink_name'],
                    "province": row['province'],
                    "city": row['city']
                }
        
        conn.close()
        
        if not region_map:
            return {"status": "No region data found", "count": 0}
        
        # 3. Connect to Elasticsearch
        es = get_es_client()
        if not es:
            return {"error": "ES Connection Failed"}
        
        # 4. Bulk update Elasticsearch
        success_count = 0
        fail_count = 0
        
        for drink_id, data in region_map.items():
            try:
                # Search for drink by drink_id
                search_res = es.search(index="liquor_integrated", body={
                    "query": {"term": {"drink_id": drink_id}},
                    "size": 1
                })
                
                if search_res['hits']['hits']:
                    es_doc_id = search_res['hits']['hits'][0]['_id']
                    
                    # Update region field only
                    es.update(
                        index="liquor_integrated",
                        id=es_doc_id,
                        body={
                            "doc": {
                                "region": {
                                    "province": data['province'],
                                    "city": data['city']
                                }
                            }
                        }
                    )
                    success_count += 1
                else:
                    fail_count += 1
                    
            except Exception as e:
                fail_count += 1
                print(f"Failed to update drink_id {drink_id}: {e}")
        
        return {
            "status": "Bulk Region Sync Complete",
            "success": success_count,
            "failed": fail_count,
            "total": len(region_map)
        }
        
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}

@router.get("/debug/sync/offline/list")
async def list_drinks_with_offline_shops():
    """
    Returns a list of drink names that have offline shops in MariaDB.
    """
    try:
        conn = get_mariadb_conn()
        with conn.cursor() as cursor:
            sql = """
                SELECT DISTINCT d.drink_name
                FROM drink_info d
                JOIN shop_drinks_bridge b ON d.drink_id = b.drink_id
                JOIN menu_shop s ON b.shop_id = s.shop_id
                WHERE s.shop_address IS NOT NULL AND CHAR_LENGTH(TRIM(s.shop_address)) > 2
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            return {"count": len(rows), "drinks": [row['drink_name'] for row in rows]}
    except Exception as e:
        return {"error": str(e)}

@router.post("/debug/sync/offline/{drink_name}")
async def sync_offline_shops_from_mariadb(drink_name: str):
    """
    Syncs Offline Shop data (with addresses) from MariaDB to Elasticsearch.
    Merges with existing Online Shop data (Mongo).
    """
    try:
        # 1. Connect to MariaDB
        conn = get_mariadb_conn()
        if not conn:
            return {"error": "MariaDB Connection Failed"}
            
        offline_shops = []
        with conn.cursor() as cursor:
            # Query for this drink
            sql = """
                SELECT d.drink_id, s.shop_name as name, b.menu_price as price, s.shop_address as address, s.shop_tel as contact
                FROM drink_info d
                JOIN shop_drinks_bridge b ON d.drink_id = b.drink_id
                JOIN menu_shop s ON b.shop_id = s.shop_id
                WHERE d.drink_name = %s
            """
            cursor.execute(sql, (drink_name,))
            rows = cursor.fetchall()
            
            for row in rows:
                if row['address'] and len(row['address'].strip()) > 2:
                    offline_shops.append({
                        "name": row['name'],
                        "price": row['price'],
                        "url": "", # No URL in menu_shop
                        "address": row['address'],
                        "contact": row.get('contact', '')
                    })
        
        conn.close()
        
        if not offline_shops:
             return {"status": "No offline shops found in MariaDB", "drink": drink_name}

        # 2. Connect to ES
        es = get_es_client()
        if not es:
            return {"error": "ES Connection Failed"}

        # 3. Get Current ES Data
        search_res = es.search(index="liquor_integrated", body={
            "query": {"match": {"name": drink_name}}
        })
        
        if not search_res['hits']['hits']:
             return {"error": "Drink not found in ES"}
             
        hit = search_res['hits']['hits'][0]
        es_doc_id = hit['_id']
        current_source = hit['_source']
        current_shops = current_source.get('selling_shops', [])
        
        # 4. Merge Logic
        # Keep existing shops ONLY if they are likely Online (no address or empty address)
        # Assuming current_shops came from Mongo (Online)
        
        merged_shops = []
        
        # Add existing online shops (filter out any that look like offline partials if needed)
        for shop in current_shops:
            # If it has no address, keep it (Online)
            if not shop.get('address') or len(shop.get('address').strip()) <= 2:
                merged_shops.append(shop)
        
        # Add new offline shops (avoid exact dups if any? usually explicit offline shops are distinct)
        merged_shops.extend(offline_shops)
        
        # 5. Update ES
        update_body = {
            "doc": {
                "selling_shops": merged_shops
            }
        }
        
        es.update(index="liquor_integrated", id=es_doc_id, body=update_body)
        
        return {
            "status": "Offline Shops Synced",
            "drink": drink_name,
            "offline_count": len(offline_shops),
            "total_shops": len(merged_shops),
            "details": offline_shops
        }
        
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}

@router.post("/debug/sync/{drink_name}")
async def sync_mongo_to_es(drink_name: str):
    """
    Syncs clean shop data from MongoDB 'products' collection to Elasticsearch.
    Fixes the corrupted text issue.
    """
    try:
        # 1. Connect to Mongo
        secrets = get_secrets()
        mongo_url = secrets.get('MONGO_URL')
        if not mongo_url:
             # Reconstruct if needed (omitted for brevity, assuming URL exists or reuse logic)
             return {"error": "Missing MONGO_URL"}

        mongo_client = MongoClient(mongo_url, serverSelectionTimeoutMS=3000)
        mongo_db = mongo_client["liquor"]
        mongo_col = mongo_db["products"] # Assuming clean data is here
        
        # 2. Connect to ES
        es = get_es_client()
        if not es:
            return {"error": "No ES connection"}
            
        # 3. Fetch all docs for this drink from Mongo
        cursor = mongo_col.find({"name": {"$regex": drink_name}}) # Use regex to be safe or exact match?
        
        shops = []
        lprice = 0
        
        mongo_docs = list(cursor)
        print(f"found {len(mongo_docs)} docs in mongo")
        
        for doc in mongo_docs:
            shop_name = doc.get('mall_name')
            price = doc.get('lprice')
            link = doc.get('link')
            
            if shop_name and price:
                shops.append({
                    "name": shop_name, # Clean name from Mongo
                    "price": int(price),
                    "url": link
                })
                
        if not shops:
            return {"status": "No shops found in Mongo to sync", "count": 0}
            
        # Calculate lowest price
        if shops:
            lprice = min([s['price'] for s in shops])
            
        # 4. Update Elasticsearch
        # First find the ES document ID (drink_id or random ID?)
        # Search ES for the drink
        search_res = es.search(index="liquor_integrated", body={
            "query": {"match": {"name": drink_name}}
        })
        
        if not search_res['hits']['hits']:
             return {"error": f"Drink '{drink_name}' not found in ES to update."}
             
        es_doc_id = search_res['hits']['hits'][0]['_id']
        
        update_body = {
            "doc": {
                "selling_shops": shops,
                "lowest_price": lprice,
                "price_source": "lowest_price" if lprice > 0 else None
            }
        }
        
        es.update(index="liquor_integrated", id=es_doc_id, body=update_body)
        
        return {
            "status": "Synced Successfully",
            "drink_name": drink_name,
            "shops_updated": len(shops),
            "lowest_price": lprice,
            "shops_preview": shops[:3]
        }

    except Exception as e:
        return {"error": str(e)}
