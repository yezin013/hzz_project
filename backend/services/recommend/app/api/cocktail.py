from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import os
import pymysql
from typing import List, Optional
from googleapiclient.discovery import build

DB_HOST = os.getenv("MARIADB_HOST", "localhost")
DB_PORT = int(os.getenv("MARIADB_PORT", 3306))
DB_USER = os.getenv("MARIADB_USER", "root")
DB_PASS = os.getenv("MARIADB_PASSWORD", "pass123#")
DB_NAME = os.getenv("MARIADB_DB", "drink")

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

router = APIRouter()

class CocktailInfo(BaseModel):
    cocktail_id: int
    cocktail_title: str
    cocktail_image_url: Optional[str] = None
    cocktail_homepage_url: Optional[str] = None


class CocktailRequest(BaseModel):
    drink_name: str

class CocktailResponse(BaseModel):
    cocktail_title: str
    cocktail_base: str
    cocktail_garnish: str
    cocktail_recipe: str
    cocktail_image_url: Optional[str] = None
    youtube_video_id: Optional[str] = None
    youtube_video_title: Optional[str] = None
    youtube_thumbnail_url: Optional[str] = None
    food_pairing_name: Optional[str] = None
    food_pairing_reason: Optional[str] = None

def search_youtube_videos(query):
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return None, None, None
        
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        search_response = youtube.search().list(
            q=query,
            part='id,snippet',
            maxResults=1,
            type='video'
        ).execute()

        if search_response.get('items'):
            video = search_response['items'][0]
            video_id = video['id']['videoId']
            title = video['snippet']['title']
            thumbnail = video['snippet']['thumbnails']['high']['url']
            return video_id, title, thumbnail
    except Exception as e:
        print(f"YouTube Search Error: {e}")
    
    return None, None, None

@router.post("/generate", response_model=CocktailResponse)
async def generate_cocktail(request: CocktailRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API Key is missing")

    try:
        genai.configure(api_key=api_key)
        # User requested "2.6flash", likely meaning the latest Flash model. Using 1.5-flash as stable default.
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        '{request.drink_name}'를 기주(베이스)로 사용하는 창의적이고 맛있는 칵테일 레시피 1개와, 
        칵테일이 아닌 '{request.drink_name}' 원주(Original Liquor) 그 자체와 가장 잘 어울리는 안주 1개를 추천해줘.
        한국어로 답변해야 해.
        
        반드시 다음 JSON 구조로 답변해줘:
        {{
            "cocktail_title": "칵테일 이름",
            "cocktail_base": "재료 목록 (예: 안동소주 2oz, 토닉워터 4oz)",
            "cocktail_garnish": "가니쉬 (예: 라임 슬라이스)",
            "cocktail_recipe": "제조법 (단계별로 설명)",
            "youtube_search_keyword": "유튜브 검색어 (예: 안동소주 칵테일 만들기)",
            "food_pairing_name": "추천 안주 이름 (예: 감자전)",
            "food_pairing_reason": "추천 이유 (한 문장)"
        }}
        
        JSON 외에 다른 말은 하지 마.
        """
        
        import time
        start_time = time.time()
        response = model.generate_content(prompt)
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        print(f"⏱️ Gemini API Time: {elapsed_time:.2f}s")
        
        if response.usage_metadata:
            print(f"💰 Gemini Token Usage: Input={response.usage_metadata.prompt_token_count}, Output={response.usage_metadata.candidates_token_count}, Total={response.usage_metadata.total_token_count}")
            
        text = response.text
        
        # Clean up code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
            
        import json
        recipe = json.loads(text)
        
        # Handle cases where Gemini returns lists instead of strings
        if isinstance(recipe.get('cocktail_base'), list):
            recipe['cocktail_base'] = ", ".join(recipe['cocktail_base'])
        if isinstance(recipe.get('cocktail_recipe'), list):
            recipe['cocktail_recipe'] = "\n".join(recipe['cocktail_recipe'])
            
        # Add a placeholder image if not present (Gemini text model doesn't generate images)
        recipe['cocktail_image_url'] = "" 
        
        # Search for YouTube video
        search_query = recipe.get('youtube_search_keyword', f"{recipe['cocktail_title']} 칵테일 만들기")
        video_id, video_title, video_thumbnail = search_youtube_videos(search_query)
        recipe['youtube_video_id'] = video_id
        recipe['youtube_video_title'] = video_title
        recipe['youtube_thumbnail_url'] = video_thumbnail
        
        return recipe

    except Exception as e:
        print(f"Gemini Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate recipe: {str(e)}")

@router.get("/random", response_model=List[CocktailInfo])
def get_random_cocktails(limit: int = 10):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT cocktail_id, cocktail_title, cocktail_image_url, cocktail_homepage_url FROM cocktail_info ORDER BY RAND() LIMIT %s"
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        
        conn.close()
        return rows
    except Exception as e:
        print(f"DB Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch cocktails")

