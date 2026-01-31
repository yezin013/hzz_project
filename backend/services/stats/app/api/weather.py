from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.utils.weather import fetch_owm_data

router = APIRouter()

class WeatherRequest(BaseModel):
    latitude: float
    longitude: float

@router.post("/current")
async def get_current_weather(request: WeatherRequest):
    """현재 날씨 정보 조회"""
    try:
        weather_data = await fetch_owm_data((request.latitude, request.longitude))
        if not weather_data:
            return {"error": "Unable to fetch weather data"}
        
        return {
            "temperature": weather_data['main']['temp'],
            "feels_like": weather_data['main']['feels_like'],
            "description": weather_data['weather'][0]['description'],
            "humidity": weather_data['main']['humidity'],
            "wind_speed": weather_data['wind']['speed']
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/recommend")
async def recommend_liquor_by_weather(adm_cd: str, city: Optional[str] = None):
    """
    날씨 기반 술 추천 API
    Frontend: WeatherBanner.tsx 호출
    """
    try:
        # 1. 날씨 정보 조회
        # adm_cd(지역코드)와 city(시군구명)을 사용하여 날씨 조회
        # city가 없으면 representative city 사용
        
        from app.utils.weather import get_weather_by_city, get_weather_by_adm_cd
        
        weather_info = {}
        if city:
             weather_info = await get_weather_by_city(adm_cd, city)
        
        # city 날씨가 없거나 실패했으면, 도(Province) 대표 날씨 조회
        if not weather_info or not weather_info.get("NOW_AIRTP"):
             # get_weather_by_adm_cd returns list, take first item
             items = await get_weather_by_adm_cd(adm_cd)
             if items:
                 weather_info = items[0] # Representative item
        
        if not weather_info:
            return {"error": "Weather data unavailable"}
            
        # 2. 날씨 상태 분석
        # Internal keys: NOW_AIRTP (temp), PCPTTN_SHP (precip type), SKY_STTS (sky)
        # PCPTTN_SHP: 0(None), 1(Rain), 2(Rain/Snow), 3(Snow), 4(Shower)
        
        temp = float(weather_info.get("NOW_AIRTP", 20))
        precip = weather_info.get("PCPTTN_SHP", "0")
        sky = weather_info.get("SKY_STTS", "1")
        
        current_weather_desc = "맑음"
        keyword = "맑은 술"
        message = "오늘 날씨엔 깔끔한 약주 한 잔 어떠세요?"
        weather_condition_key = "clear" # For search/region (optional)

        # Logic
        # Logic
        if precip == "1" or precip == "4": # Rain
            current_weather_desc = "비"
            keyword = "파전엔 막걸리"
            message = f"현재 기온 {int(temp)}도, 비가 내리고 있습니다.\n빗소리 들으며 파전에 막걸리 한 잔 어떠세요?"
            weather_condition_key = "rain"
        elif precip == "3": # Snow
            current_weather_desc = "눈" # Snow
            keyword = "따뜻한 술"
            message = f"현재 기온 {int(temp)}도, 눈이 내리는 날이네요.\n몸을 녹여줄 도수 높은 술이 준비되어 있습니다."
            weather_condition_key = "snow"
        elif precip == "2": # Sleet
            current_weather_desc = "진눈깨비"
            keyword = "감성적인 술"
            message = f"현재 기온 {int(temp)}도, 진눈깨비가 흩날립니다.\n이런 날엔 운치 있는 한 잔이 제격이죠."
            weather_condition_key = "rain"
        else:
            # No precip, check temp & sky
            if temp >= 28:
                current_weather_desc = "무더움"
                keyword = "시원한 술"
                message = f"현재 기온 {int(temp)}도로 무더운 날씨입니다.\n더위를 싹 날려버릴 시원한 술을 추천해드릴게요!"
                weather_condition_key = "hot"
            elif temp <= 5:
                current_weather_desc = "추움"
                keyword = "도수 높은 술"
                message = f"현재 기온 {int(temp)}도로 쌀쌀한 날씨네요.\n추위를 녹여줄 따뜻하거나 독한 술이 어울려요."
                weather_condition_key = "cold"
            elif sky == "3" or sky == "4":
                current_weather_desc = "흐림"
                keyword = "분위기 있는 술"
                message = f"현재 기온 {int(temp)}도, 흐린 하늘입니다.\n이런 날엔 센치한 기분에 어울리는 약주가 딱이죠."
                weather_condition_key = "clear" # Fallback
            else:
                current_weather_desc = "맑음"
                keyword = "깔끔한 술"
                message = f"현재 기온 {int(temp)}도, 화창하고 맑은 날씨입니다!\n오늘 같은 날엔 기분 좋은 술 한 잔 어떠세요?"
                weather_condition_key = "clear"

        # 3. Available Cities for Dropdown (Optional but requested by frontend)
        from app.utils.weather import PROVINCE_CITY_LIST
        available_cities = PROVINCE_CITY_LIST.get(adm_cd, [])

        return {
            "city": weather_info.get("SGG_NM", city or "알 수 없음"),
            "temperature": temp,
            "weather": current_weather_desc, 
            "message": message,
            "keyword": keyword,
            "liquors": [], # Recommendations could be fetched here or frontend calls /search/region separately?
                           # Frontend checks `weatherData.liquors` but current logic in WeatherBanner doesn't seem to iterate it much?
                           # Actually Frontend just shows keyword/message. 
                           # If we want liquors, we could fetch them, but for now let's return empty to satisfy interface.
                           # Actually, let's fetch 3 recommendations using the weather condition key if possible?
                           # Avoiding circular dependency or complexity since search is in another service (though shared monorepo codebase).
                           # For now, keep it simple.
            "available_cities": available_cities
        }
    except Exception as e:
        print(f"Recommend Error: {e}")
        return {"error": str(e)}
