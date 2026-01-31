import os
import httpx
import redis
import json
import logging

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis Connection
try:
    redis_client = redis.StrictRedis(
        host=os.getenv("REDIS_HOST"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD"),
        decode_responses=True,
        socket_timeout=2
    )
    # redis_client.ping() # Optional check on init
except Exception as e:
    logger.error(f"❌ Redis Connection Failed (Chatbot): {e}")
    redis_client = None

async def fetch_owm_data(coords: tuple):
    """
    OpenWeatherMap API를 사용하여 날씨 정보 가져오기 (Redis Caching Applied)
    coords: (latitude, longitude)
    """
    api_key = os.getenv("OWM_API_KEY")
    if not api_key:
        print("⚠️ OWM_API_KEY not set")
        return None
    
    lat, lon = coords
    
    # 1. Check Redis Cache
    if redis_client:
        try:
            # Round coordinates to 2 decimal places to increase cache hit rate for nearby locations
            # 0.01 degree is approx 1.1km
            lat_key = round(lat, 2)
            lon_key = round(lon, 2)
            cache_key = f"weather:chatbot:{lat_key}:{lon_key}"
            
            cached = redis_client.get(cache_key)
            if cached:
                print(f"🎯 Weather Cache Hit: {cache_key}")
                return json.loads(cached)
        except Exception as e:
            print(f"⚠️ Redis Read Error: {e}")

    # 2. Fetch from API
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=kr"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            response.raise_for_status()
            data = response.json()
            
            # 3. Save to Redis Cache
            if redis_client and data:
                try:
                    lat_key = round(lat, 2)
                    lon_key = round(lon, 2)
                    cache_key = f"weather:chatbot:{lat_key}:{lon_key}"
                    
                    # Cache for 2 hours (7200s) like stats service
                    redis_client.setex(cache_key, 7200, json.dumps(data))
                except Exception as e:
                    print(f"⚠️ Redis Write Error: {e}")
            
            return data
    except Exception as e:
        print(f"❌ Weather API Error: {e}")
        return None
