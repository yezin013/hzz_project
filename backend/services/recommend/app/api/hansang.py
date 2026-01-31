from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import os
import pymysql
import json
from typing import List, Optional

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

class SpecialtyProduct(BaseModel):
    local_id: int
    province: str
    city_county: str
    contents_name: str
    imgurl: Optional[str] = None
    linkurl: Optional[str] = None

class HansangItem(BaseModel):
    name: str
    image_url: Optional[str] = None
    reason: str
    link_url: Optional[str] = None
    specialty_used: Optional[str] = None  # Which specialty product was used

class HansangRequest(BaseModel):
    drink_name: str
    province: str
    city: Optional[str] = None
    drink_description: Optional[str] = None  # Fallback when no specialties

class HansangResponse(BaseModel):
    items: List[HansangItem]

@router.get("/specialties", response_model=List[SpecialtyProduct])
def get_regional_specialties(province: str, city: Optional[str] = None, limit: int = 20):
    """
    Get regional specialty products by province and city
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if city:
            query = """
                SELECT local_id, province, city_county, contents_name, imgurl, linkurl 
                FROM local_specialties 
                WHERE province = %s AND city_county = %s 
                LIMIT %s
            """
            cursor.execute(query, (province, city, limit))
        else:
            query = """
                SELECT local_id, province, city_county, contents_name, imgurl, linkurl 
                FROM local_specialties 
                WHERE province = %s 
                LIMIT %s
            """
            cursor.execute(query, (province, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return rows
    except Exception as e:
        print(f"DB Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch specialty products: {str(e)}")

@router.get("/specialties/by-drink/{drink_id}", response_model=List[SpecialtyProduct])
def get_specialties_by_drink(drink_id: int, limit: int = 20):
    """
    Get specialty products linked to a specific drink via the bridge table
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT ls.local_id, ls.province, ls.city_county, ls.contents_name, ls.imgurl, ls.linkurl
            FROM local_specialties ls
            JOIN drink_local_specialty_bridge dlsb ON ls.local_id = dlsb.local_id
            WHERE dlsb.drink_id = %s
            LIMIT %s
        """
        cursor.execute(query, (drink_id, limit))
        rows = cursor.fetchall()
        conn.close()
        
        return rows
    except Exception as e:
        print(f"DB Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch specialty products for drink: {str(e)}")

@router.post("/recommend", response_model=HansangResponse)
async def generate_hansang_recommendations(request: HansangRequest):
    """
    Generate AI-powered smart hansang (traditional Korean table setting) recommendations
    Combines existing food pairings with regional specialty products
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API Key is missing")

    try:
        # First, fetch regional specialty products
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if request.city:
            # Handle both "여주" and "여주시" matching
            query = """
                SELECT contents_name, imgurl, linkurl 
                FROM local_specialties 
                WHERE province = %s AND (city_county = %s OR city_county LIKE CONCAT(%s, '%%'))
                LIMIT 20
            """
            print(f"🔎 Querying: province='{request.province}', city='{request.city}'")
            cursor.execute(query, (request.province, request.city, request.city))
        else:
            query = """
                SELECT contents_name, imgurl, linkurl 
                FROM local_specialties 
                WHERE province = %s 
                LIMIT 20
            """
            cursor.execute(query, (request.province,))
        
        specialties = cursor.fetchall()
        conn.close()
        
        # DEBUG: Log retrieved specialties
        print(f"🔍 Retrieved {len(specialties)} specialties for {request.province} {request.city or ''}")
        if specialties:
            specialty_names = [s['contents_name'] for s in specialties]
            print(f"📦 Specialty products: {', '.join(specialty_names[:10])}")  # Show first 10
        
        # Dual-mode recommendation system
        use_specialties = len(specialties) > 0
        
        # Treat empty string as None
        description = request.drink_description.strip() if request.drink_description else None
        has_description = bool(description)
        
        if not use_specialties and not has_description:
            # Fallback: Generate generic Korean food pairings
            print(f"⚠️ No specialties and no description for {request.drink_name}, using generic recommendations")
            use_generic = True
        else:
            use_generic = False
        
        # Generate AI recommendations using Gemini with SMART prompt
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        location_str = f"{request.province} {request.city}" if request.city else request.province
        
        if use_specialties:
            # MODE 1: Use regional specialties
            specialty_names = [s['contents_name'] for s in specialties]
            specialty_dict = {s['contents_name']: s for s in specialties}
            
            prompt = f"""당신은 전통주 전문가이자 한식 요리사입니다.

### 전통주 정보
- 술 이름: {request.drink_name}
- 지역: {location_str}

### 지역 특산물 목록
{', '.join(specialty_names)}

### 임무
위 지역 특산물을 활용하여 '{request.drink_name}'와 가장 잘 어울리는 한상차림 안주 5가지를 추천해주세요.

### 추천 규칙
1. **각 음식마다 정확히 하나의 특산물만 사용할 것** (중요!)
2. 위 특산물 목록에 있는 정확한 이름을 specialty_used에 복사할 것
3. 여러 특산물을 조합하지 말고, 하나만 선택할 것
4. 전통주와의 페어링을 고려할 것
5. 실제로 만들 수 있는 현실적인 음식일 것

### 출력 형식 (JSON)
{{
    "items": [
        {{
            "name": "특산물을 활용한 음식 이름",
            "specialty_used": "사용한 특산물 이름 (위 목록에 있는 정확한 이름)",
            "reason": "이 술과 어울리는 이유 (한 문장, 20자 이내)"
        }}
    ]
}}

**중요사항**:
- specialty_used에는 반드시 위 특산물 목록에 있는 **정확한 이름 하나만** 사용
- 쉼표(,)로 구분하거나 여러 개를 넣지 말 것
- 5개 추천할 것
- reason은 간결하게 한 문장으로 작성
- JSON 형식만 출력하고 다른 말은 하지 말 것
"""
        else:
            #  MODE 2/3: Description-based or generic
            if has_description:
                # MODE 2: Use drink description
                print(f"⚠️ No specialties found for {location_str}, using drink description fallback")
                
                prompt = f"""당신은 전통주 전문가이자 한식 요리사입니다.

### 전통주 정보
- 술 이름: {request.drink_name}
- 설명: {description}

### 임무
위 전통주의 특징을 분석하여 가장 잘 어울리는 한상차림 안주 5가지를 추천해주세요.

### 추천 규칙
1. 술의 맛, 향, 특징을 고려할 것
2. 전통주와의 페어링을 고려할 것
3. 실제로 만들 수 있는 현실적인 한국 음식일 것
4. 각 안주가 이 술과 어울리는 이유를 간단히 설명할 것
5. 다양한 조리법의 안주를 추천할 것 (구이, 찜, 전, 나물, 회 등)

### 출력 형식 (JSON)
{{
    "items": [
        {{
            "name": "안주 이름",
            "reason": "이 술과 어울리는 이유 (한 문장, 30자 이내)"
        }}
    ]
}}

**중요사항**:
- 5개 추천할 것
- reason은 간결하게 한 문장으로 작성
- JSON 형식만 출력하고 다른 말은 하지 말 것
"""
            else:
                # MODE 3: Generic Korean traditional pairings
                print(f"⚠️ Using generic Korean food pairing recommendations for {request.drink_name}")
                
                prompt = f"""당신은 전통주 전문가이자 한식 요리사입니다.

### 전통주 정보
- 술 이름: {request.drink_name}

### 임무
한국 전통주와 잘 어울리는 대표적인 한상차림 안주 5가지를 추천해주세요.

### 추천 규칙
1. 한국 전통주와 일반적으로 잘 어울리는 음식일 것
2. 다양한 조리법을 포함할 것 (구이, 찜, 전, 나물, 무침 등)
3. 실제로 흔히 먹는 대중적인 한국 음식일 것
4. 각 안주가 전통주와 어울리는 이유를 간단히 설명할 것

### 출력 형식 (JSON)
{{
    "items": [
        {{
            "name": "안주 이름",
            "reason": "전통주와 어울리는 이유 (한 문장, 30자 이내)"
        }}
    ]
}}

**중요사항**:
- 5개 추천할 것
- reason은 간결하게 한 문장으로 작성
- JSON 형식만 출력하고 다른 말은 하지 말 것
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
        
        result = json.loads(text.strip())
        
        # Enrich items with image URLs and link URLs from database
        enriched_items = []
        
        if use_specialties:
            # MODE 1: Match specialty products with DB data
            specialty_dict = {s['contents_name']: s for s in specialties}
            
            print(f"🔍 Matching AI results with DB specialties...")
            for item in result.get('items', []):
                # Get the specialty name from the item
                specialty_name = item.get('specialty_used', '')
                specialty_data = specialty_dict.get(specialty_name)
                
                # DEBUG: Log matching
                if specialty_data:
                    print(f"  ✅ Matched: '{specialty_name}' → image found")
                else:
                    print(f"  ❌ NOT matched: '{specialty_name}' (AI used this, but not in DB)")
                    print(f"     Available in DB: {list(specialty_dict.keys())[:5]}")
                
                enriched_items.append(HansangItem(
                    name=item['name'],
                    image_url=specialty_data['imgurl'] if specialty_data else None,
                    reason=item['reason'],
                    link_url=specialty_data['linkurl'] if specialty_data else None,
                    specialty_used=specialty_name if specialty_data else None
                ))
                
                # DEBUG: Log URL being returned
                img_url = specialty_data['imgurl'] if specialty_data else None
                if img_url:
                    print(f"     📷 Image URL: {img_url[:80]}...")
                else:
                    print(f"     ❌ No image URL")
        else:
            # MODE 2/3: Description-based or generic, no images/links
            for item in result.get('items', []):
                enriched_items.append(HansangItem(
                    name=item['name'],
                    image_url=None,
                    reason=item['reason'],
                    link_url=None
                ))
        
        return HansangResponse(items=enriched_items)
        
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        print(f"Response text: {text}")
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        print(f"Gemini Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate hansang recommendations: {str(e)}")

