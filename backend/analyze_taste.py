
import os
import sys
import json
import pymysql
import time
import google.generativeai as genai
from dotenv import load_dotenv

# ==========================================
# 1. Configuration & Setup
# ==========================================

# Load environment variables
# Try loading from backend.env or root .env
env_path = os.path.join(os.path.dirname(__file__), "backend.env")
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"📋 Loaded env from {env_path}")
else:
    load_dotenv() # Try default .env

# DB Connection
DB_HOST = os.environ.get("MARIADB_HOST", "localhost")
DB_PORT = int(os.environ.get("MARIADB_PORT", "3306"))
DB_USER = os.environ.get("MARIADB_USER", "root")
DB_PASS = os.environ.get("MARIADB_PASSWORD", "pass123#")
DB_NAME = os.environ.get("MARIADB_DB", "drink")

# Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Data Path
DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "../data/비정형/전통주 지식백과.json")

def get_db_conn():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4'
    )

def configure_gemini():
    if not GEMINI_API_KEY:
        print("❌ Error: GEMINI_API_KEY not found in environment variables.")
        sys.exit(1)
    
    # Debug: Print key status
    print(f"🔑 Gemini API Key loaded (Length: {len(GEMINI_API_KEY)}, Starts with: {GEMINI_API_KEY[:4]}...)")
    
    genai.configure(api_key=GEMINI_API_KEY)
    # Using gemini-flash-latest as verified in available models
    return genai.GenerativeModel('gemini-2.5-flash')

# ==========================================
# 2. Data Loading (Encyclopedia)
# ==========================================
def load_encyclopedia():
    """Load encyclopedia data for ingredients lookup"""
    print("📚 Loading Encyclopedia data...")
    data_map = {}
    
    # Try multiple paths for robustness
    paths = [
        DATA_FILE_PATH,
        os.path.join(os.path.dirname(__file__), "../../data/비정형/전통주 지식백과.json"),
        "../../data/비정형/전통주 지식백과.json"
    ]
    
    loaded = False
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    items = json.load(f)
                    for item in items:
                        norm_name = item.get('name', '').replace(' ', '')
                        data_map[norm_name] = item
                print(f"✅ Loaded {len(data_map)} encyclopedia entries from {path}")
                loaded = True
                break
            except Exception as e:
                print(f"⚠️ Failed to load {path}: {e}")
    
    if not loaded:
        print("⚠️ Encyclopedia file not found. Ingredients will be empty.")
        
    return data_map

def get_drink_details(name, encyclopedia):
    """Find ingredients and full description from encyclopedia"""
    norm_name = name.replace(' ', '').strip()
    entry = encyclopedia.get(norm_name)
    
    ingredients = "정보 없음"
    description = ""
    
    if entry:
        naver = entry.get('naver', {})
        ingredients = naver.get('raw_info_table', {}).get('원재료', '정보 없음')
        
        # Get long description
        sections = naver.get('sections', [])
        if sections:
            description = sections[0].get('text', '')
            
    return ingredients, description

# ==========================================
# 3. AI Analysis (Gemini)
# ==========================================

def analyze_taste_with_ai(model, name, intro, ingredients, description):
    """
    Analyzes drink info to generate 5-axis taste profile.
    Returns: JSON dict {sweetness, sourness, freshness, body, aroma, balance, season}
    """
    
    prompt = f"""
    You are a Sommelier for Korean Traditional Alcohol.
    Analyze the provided drink information (Name, Ingredients, Description) and estimate its taste profile numerically.
    
    [Criteria for Season & Taste - IMPORTANT]
    Please follow this specific scoring guide based on fermentation time (if mentioned) or general impression:

    1. **Spring (봄)**: Short fermentation (1-3 days)
       - TARGET SCORE: Sweetness 5, Sourness 1, Freshness 2
    
    2. **Summer (여름)**: Medium fermentation (4-6 days)
       - TARGET SCORE: Sweetness 3, Sourness 1, Freshness 4
    
    3. **Autumn (가을)**: Long fermentation (7-9 days)
       - TARGET SCORE: Sweetness 2, Sourness 3, Freshness 5
    
    4. **Winter (겨울)**: Very long fermentation (10+ days)
       - TARGET SCORE: Sweetness 1, Sourness 3, Freshness 4
    
    5. **NOTE**: You MUST choose one of the 4 seasons above. Do NOT use "Four Seasons" or "All". 
       If unsure, choose the season that best fits the mood or alcohol type (e.g., High Body -> Winter, Carbonated -> Summer).

    [Drink Info]
    Name: {name}
    Intro: {intro}
    Ingredients: {ingredients}
    Description: {description}

    OUTPUT FORMAT:
    Return ONLY a valid JSON object.
    {{
        "sweetness": int (0-5),  // Follow target scores above
        "sourness": int (0-5),   // Follow target scores above
        "freshness": int (0-5),  // Follow target scores above
        "body": int (0-5),       // Infer from description
        "aroma": int (0-5),      // Infer from description
        "balance": int (0-5),    // Infer from description
        "season": string         // "봄", "여름", "가을", "겨울" (Must choose one)
    }}
    """
    
    max_retries = 5
    base_delay = 10
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            text = response.text
            
            # Parse JSON from output
            clean_json = text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            return data
            
        except Exception as e:
            if "429" in str(e):
                wait_time = base_delay * (2 ** attempt)
                print(f"⏳ Quota exceeded (429). Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                print(f"❌ AI Analysis Failed for {name}: {e}")
                break
    
    # Return default neutral values if all retries fail
    print(f"⚠️ Using default values for {name} due to repeated errors.")
    return {
        "sweetness": 2, "sourness": 2, "freshness": 2, 
        "body": 2, "aroma": 2, "balance": 3, "season": "사계절"
    }

# ==========================================
# 4. Main Execution
# ==========================================
def main():
    print("🚀 Starting AI Taste Analysis (Gemini Powered)...")
    
    # 1. Load Resources
    encyclopedia = load_encyclopedia()
    model = configure_gemini()
    conn = get_db_conn()
    
    try:
        with conn.cursor() as cursor:
            # 2. Reset 'Four Seasons' data (User Request)
            print("🧹 Cleaning up 'Four Seasons' data to re-analyze...")
            cleanup_sql = "DELETE FROM taste_profile WHERE season = '사계절'"
            cursor.execute(cleanup_sql)
            conn.commit()
            print("✨ 'Four Seasons' data reset complete.")

            # 3. Check for missing data
            print("🔍 Finding drinks without taste profile...")
            
            sql = """
                SELECT d.drink_id, d.drink_name, d.drink_intro
                FROM drink_info d
                LEFT JOIN taste_profile t ON d.drink_id = t.drink_id
                WHERE t.drink_id IS NULL
            """
            cursor.execute(sql)
            missing_drinks = cursor.fetchall()
            print(f"📋 Found {len(missing_drinks)} drinks to analyze.")
            
            if not missing_drinks:
                print("✨ All drinks have taste profiles! Exiting.")
                return

            # 3. Process loop
            count = 0
            for drink in missing_drinks:
                d_id = drink['drink_id']
                name = drink['drink_name']
                intro = drink['drink_intro']
                
                print(f"🤖 Analyzing [{count+1}/{len(missing_drinks)}]: {name}...")
                
                # Enrich data
                ingredients, description = get_drink_details(name, encyclopedia)
                
                # AI Call
                result = analyze_taste_with_ai(model, name, intro, ingredients, description)
                
                # Insert DB
                insert_sql = """
                    INSERT INTO taste_profile 
                    (drink_id, drink_name, sweetness, sourness, freshness, body, aroma, balance, season)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_sql, (
                    d_id, name,
                    result.get('sweetness', 2),
                    result.get('sourness', 2),
                    result.get('freshness', 2),
                    result.get('body', 2),
                    result.get('aroma', 2),
                    result.get('balance', 3),
                    result.get('season', '사계절')
                ))
                
                conn.commit()
                count += 1
                
                # Rate limit (Gemini Free has limits ~10-15 RPM)
                # Sleep safely to respect quota
                print("💤 Sleeping 15s to respect rate limit...")
                time.sleep(15.0)
                
            print(f"✅ Successfully added {count} taste profiles.")
            
    except Exception as e:
        print(f"❌ Critical Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
