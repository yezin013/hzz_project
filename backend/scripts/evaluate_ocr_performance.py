
import sys
import os
import asyncio
import json
import random
import httpx
import time
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import pandas as pd
from difflib import SequenceMatcher
import boto3

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# In-cluster: Env vars are already injected by K8s Secret
# No need to load .env or fetch from AWS Secrets Manager manually

# Config from Env
ES_HOSTS = os.getenv("ELASTICSEARCH_HOSTS")
ES_USER = os.getenv("ELASTICSEARCH_USERNAME")
ES_PASS = os.getenv("ELASTICSEARCH_PASSWORD")

CLOVA_API_URL = os.getenv("CLOVA_OCR_API_URL")
CLOVA_SECRET_KEY = os.getenv("CLOVA_OCR_SECRET_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not ES_HOSTS:
    print("❌ ELASTICSEARCH_HOSTS not found in environment.")
    # Fallback for testing if env is missing (unlikely in pod)
    sys.exit(1)

# Connect to ES
# In K8s, hosts might be internal service names like "elasticsearch:9200"
es_url_list = [f"https://{h.strip()}:9200" if not h.startswith("http") else h for h in ES_HOSTS.split(",")]
# Handling internal vs external: usually K8s internal use http/9200 or https/9200 depending on setup.
# If previous logic worked with https, try that.
# Actually, let's allow the library to handle scheme if provided.

print(f"🔌 Connecting to ES: {es_url_list}...")

es = Elasticsearch(
    es_url_list,
    basic_auth=(ES_USER, ES_PASS) if ES_USER else None,
    verify_certs=False,
    ssl_show_warn=False
)

import google.generativeai as genai
import uuid
import base64

# --- 1. Core OCR Logic (Adapted for Script) ---

async def call_clova(content: bytes):
    request_json = {
        "images": [{"format": "jpg", "name": "demo", "data": base64.b64encode(content).decode("utf-8")}],
        "requestId": str(uuid.uuid4()),
        "version": "V2",
        "timestamp": int(round(time.time() * 1000))
    }
    headers = {"X-OCR-SECRET": CLOVA_SECRET_KEY, "Content-Type": "application/json"}
    
    url = CLOVA_API_URL.replace("http://", "https://") if CLOVA_API_URL else ""
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, json=request_json)
            if resp.status_code == 200:
                result = resp.json()
                text_list = []
                for image in result.get("images", []):
                    for field in image.get("fields", []):
                        text_list.append(field.get("inferText", ""))
                return " ".join(text_list)
    except Exception as e:
        print(f"Clova Error: {e}")
    return ""

def call_gemini(content: bytes):
    if not GEMINI_API_KEY: return {}
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = """한국 전통주 라벨입니다. 
    다음 정보를 JSON으로 정확히 추출하세요. 
    찾을 수 없으면 빈 문자열로 두세요.
    {
        "product_name": "제품명 (가장 큰 글씨)",
        "brewery": "양조장/제조사 (작은 글씨, 보통 '주식회사' '도가' 등이 붙음)"
    }"""
    
    try:
        response = model.generate_content(
            [prompt, {"mime_type": "image/jpeg", "data": content}],
            generation_config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text)
        return data
    except Exception as e:
        print(f"Gemini Error: {e}")
        return {}

async def search_es_candidates(query, size=5):
    if not query: return []
    try:
        # Search ES name field
        res = es.search(index="liquor_integrated", body={
            "query": {
                "match": {
                    "name": {"query": query, "fuzziness": "AUTO"}
                }
            },
            "size": size
        })
        return res['hits']['hits']
    except:
        return []

# --- 2. Advanced Ensemble Logic (V2) ---

# --- 2. Advanced Ensemble Logic (V3: Multi-Source Candidates) ---

async def run_ensemble_v3(g_data, c_text):
    """
    Ensemble V3: Multi-Source Search + Re-ranking
    Strategies:
    1. Search by Gemini Product Name
    2. Search by Clova 'Longest Word' (Heuristic)
    3. Search by Gemini Brewery (if exists) -> Filtered Search
    """
    g_name = g_data.get("product_name", "")
    g_brewery = g_data.get("brewery", "")
    
    candidates_map = {} # name -> hit_source
    
    # helper to add hits
    def add_hits(hits, source_label):
        for h in hits:
            n = h['_source']['name']
            if n not in candidates_map:
                h['origin_query'] = source_label
                candidates_map[n] = h
    
    # Source A: Gemini Name
    if g_name:
        hits_g = await search_es_candidates(g_name, size=5)
        add_hits(hits_g, "gemini_name")
        
    # Source B: Clova Heuristic (Longest Korean Word)
    # Clova returns space-separated tokens. Let's find longest Korean token.
    c_tokens = [w for w in c_text.split() if len(w) >= 2 and any('\u3131' <= char <= '\uD7A3' for char in w)]
    c_tokens.sort(key=len, reverse=True)
    c_best_guess = c_tokens[0] if c_tokens else ""
    
    if c_best_guess and c_best_guess != g_name:
        hits_c = await search_es_candidates(c_best_guess, size=5)
        add_hits(hits_c, "clova_guess")
        
    # Source C: Gemini Brewery (Context Search)
    if g_brewery:
        # Search for products where brewery.name matches
        try:
            res = es.search(index="liquor_integrated", body={
                "query": {
                    "match": {
                        "brewery.name": {"query": g_brewery, "fuzziness": "AUTO"}
                    }
                },
                "size": 5
            })
            add_hits(res['hits']['hits'], "gemini_brewery")
        except:
            pass

    # Re-ranking logic
    best_hit = None
    max_score = -1.0
    reason = "None"
    
    
    for name, hit in candidates_map.items():
        source = hit['_source']
        db_name = source.get('name', '')
        db_brewery = source.get('brewery', {}).get('name', '') or ""
        
        score = 0
        
        # 1. Name Similarity (Base) - Check against BOTH Gemini and Clova
        sim_g = SequenceMatcher(None, g_name, db_name).ratio() * 100 if g_name else 0
        sim_c = SequenceMatcher(None, c_best_guess, db_name).ratio() * 100 if c_best_guess else 0
        score += max(sim_g, sim_c)
        
        # 2. Brewery Bonus (Verification)
        brewery_match = False
        if g_brewery and db_brewery:
            if g_brewery in db_brewery or db_brewery in g_brewery:
                score += 40 # Confirmed by Gemini
                brewery_match = True
        
        if db_brewery and len(db_brewery) > 2 and db_brewery in c_text:
             score += 30 # Confirmed by Clova text
             brewery_match = True
             
        # 3. Origin Bonus
        if hit.get('origin_query') == 'gemini_brewery':
            score += 10 # High trust if found via brewery search
            
        if score > max_score:
            max_score = score
            best_hit = db_name
            reason = f"Score {score:.0f} (Src: {hit.get('origin_query')})"
            
    return best_hit, reason

# --- 2.5 Pipeline Strategy (User Idea: Clova -> Gemini) ---

def call_gemini_parser(text_content):
    if not GEMINI_API_KEY: return {}
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    The following is raw text extracted from a Korean liquor label using OCR.
    It is unstructured and may contain noise.
    Extract the 'product_name' (most likely the name of the liquor) and 'brewery' (manufacturer).
    
    Raw Text:
    {text_content}
    
    Response JSON only:
    {{ "product_name": "...", "brewery": "..." }}
    """
    
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except:
        return {}

async def run_pipeline_strategy(c_text):
    """
    Strategy 4: Pipeline
    Clova (Vision) -> Raw Text -> Gemini (Parser) -> Structured Data -> Search ES
    """
    # 1. Use Gemini to parse Clova's output
    parsed = call_gemini_parser(c_text)
    p_name = parsed.get("product_name", "")
    p_brewery = parsed.get("brewery", "")
    
    if not p_name: return "", "Pipeline Failed"
    
    # 2. Use the parsed name to search ES
    candidates = await search_es_candidates(p_name, size=5)
    
    # 3. Simple Re-ranking (Name Sim + Brewery Check)
    best_hit = None
    max_score = -1.0
    
    for hit in candidates:
        source = hit['_source']
        db_name = source.get('name', '')
        db_brewery = source.get('brewery', {}).get('name', '') or ""
        
        score = SequenceMatcher(None, p_name, db_name).ratio() * 100
        
        if p_brewery and db_brewery and (p_brewery in db_brewery or db_brewery in p_brewery):
            score += 20
            
        if score > max_score:
            max_score = score
            best_hit = db_name
            
    return best_hit, f"Pipeline (Score {max_score:.0f})"

# --- 2.6 Ensemble V4 (Hybrid: V3 + Pipeline) ---

async def run_ensemble_v4(g_data, c_text):
    """
    Ensemble V4: The Ultimate Hybrid
    Combines:
    1. Gemini Vision Name
    2. Gemini Vision Brewery
    3. Clova Heuristic (Longest Word)
    4. Pipeline (Clova Text -> Gemini Parser)
    
    Then applies the Unified Re-ranking Logic.
    """
    # 1. Gather all raw inputs
    g_name = g_data.get("product_name", "")
    g_brewery = g_data.get("brewery", "")
    
    # Pipeline step (Text -> Structure)
    p_data = call_gemini_parser(c_text)
    p_name = p_data.get("product_name", "")
    p_brewery = p_data.get("brewery", "") or g_brewery # Fallback to Vision brewery if Parser misses it
    
    c_tokens = [w for w in c_text.split() if len(w) >= 2 and any('\u3131' <= char <= '\uD7A3' for char in w)]
    c_tokens.sort(key=len, reverse=True)
    c_best_guess = c_tokens[0] if c_tokens else ""
    
    # 2. Candidate Pooling
    candidates_map = {} # name -> hit
    
    async def collect_candidates(query, source_label):
        if not query: return
        try:
            hits = await search_es_candidates(query, size=5)
            for h in hits:
                n = h['_source']['name']
                if n not in candidates_map:
                    h['origin_query'] = source_label
                    candidates_map[n] = h
        except: pass

    await collect_candidates(g_name, "gemini_vision")
    await collect_candidates(p_name, "pipeline_parser") # This is the V4 addition
    if c_best_guess and c_best_guess != g_name:
        await collect_candidates(c_best_guess, "clova_heuristic")
        
    # Brewery Context Search (Strong Signal)
    if g_brewery:
        try:
            res = es.search(index="liquor_integrated", body={
                "query": {"match": {"brewery.name": {"query": g_brewery, "fuzziness": "AUTO"}}},
                "size": 5
            })
            for h in res['hits']['hits']:
                 n = h['_source']['name']
                 if n not in candidates_map:
                    h['origin_query'] = "brewery_context"
                    candidates_map[n] = h
        except: pass

    # 3. Unified Re-ranking
    best_hit = None
    max_score = -1.0
    reason = "None"
    
    for name, hit in candidates_map.items():
        source = hit['_source']
        db_name = source.get('name', '')
        db_brewery = source.get('brewery', {}).get('name', '') or ""
        
        score = 0
        
        # A. Name Similarity (Compare against ALL signals)
        sim_g = SequenceMatcher(None, g_name, db_name).ratio() * 100 if g_name else 0
        sim_p = SequenceMatcher(None, p_name, db_name).ratio() * 100 if p_name else 0
        sim_c = SequenceMatcher(None, c_best_guess, db_name).ratio() * 100 if c_best_guess else 0
        
        # Take the max similarity among all sources (Trust the best eye)
        score += max(sim_g, sim_p, sim_c)
        
        # B. Brewery Verification (Crucial)
        # Check if DB brewery matches EITHER GeminiVision OR Pipeline OR RawClova
        brewery_confirmed = False
        target_breweries = [b for b in [g_brewery, p_brewery] if b]
        
        if db_brewery:
            # 1. Check against structured extractions
            for tb in target_breweries:
                if tb in db_brewery or db_brewery in tb:
                    score += 40
                    brewery_confirmed = True
                    break
            
            # 2. Check against raw text (Last resort)
            if not brewery_confirmed and len(db_brewery) > 2 and db_brewery in c_text:
                score += 30
                
        # C. Origin Bonus
        origin = hit.get('origin_query')
        if origin == 'gemini_vision': score += 5
        if origin == 'pipeline_parser': score += 10 # High trust in Parser logic
        if origin == 'brewery_context': score += 15 # Specialized search
        
        if score > max_score:
            max_score = score
            best_hit = db_name
            reason = f"Score {score:.0f} ({origin})"
            
    return best_hit, reason

async def evaluate():
    print("🚀 Starting OCR Evaluation...")
    
    # 1. Fetch Random Docs
    try:
        resp = es.search(index="liquor_integrated", body={
            "query": {"exists": {"field": "image_url"}},
            "size": 20,
            "sort": [{"_script": {"type": "number", "script": "Math.random()", "order": "asc"}}]
        })
        docs = resp['hits']['hits']
    except Exception as e:
        print(f"❌ ES Connect Error: {e}")
        return

    results = []
    
    print(f"🧪 Testing {len(docs)} images...")
    
    async with httpx.AsyncClient() as client:
        for i, doc in enumerate(docs):
            source = doc['_source']
            name = source['name']
            img_url = source.get('image_url')
            
            if not img_url: continue
            
            print(f"[{i+1}/{len(docs)}] Processing '{name}'...")
            
            # Download Image
            try:
                img_resp = await client.get(img_url, timeout=5.0)
                if img_resp.status_code != 200: continue
                img_bytes = img_resp.content
            except:
                print("  ⚠️ Image download failed")
                continue
                
            # Run Models
            start = time.time()
            g_data = call_gemini(img_bytes)
            c_res = await call_clova(img_bytes)
            
            g_name = g_data.get("product_name", "")
            
            # 1. Clova Only Heuristic
            # Heuristic: Take the first line that is korean and not in blocklist, or just the longest word
            c_lines = c_res.split()
            c_name_heuristic = ""
            for word in c_lines:
                if len(word) >= 2 and any('\u3131' <= char <= '\uD7A3' for char in word): # Korean check
                    c_name_heuristic = word
                    break
            if not c_name_heuristic and c_lines:
                c_name_heuristic = c_lines[0] # Fallback
            
            # 2. Run Ensemble V3
            e_res_v3, e_method_v3 = await run_ensemble_v3(g_data, c_res)
            
            # 3. Run Pipeline (User Idea)
            p_res, p_method = await run_pipeline_strategy(c_res)
            
            # 4. Run Ensemble V4 (Hybrid)
            e_res_v4, e_method_v4 = await run_ensemble_v4(g_data, c_res)
            
            if not p_res: p_res = ""
            if not e_res_v4: e_res_v4 = ""
            
            # Calculate Similarity (Accuracy)
            def similarity(a, b):
                if not a or not b: return 0.0
                return SequenceMatcher(None, str(a).replace(" ",""), str(b).replace(" ","")).ratio() * 100
            
            g_acc = similarity(name, g_data.get("product_name", ""))
            v3_acc = similarity(name, e_res_v3) # V3 from before
            v4_acc = similarity(name, e_res_v4) # V4
            
            results.append({
                "Real Name": name,
                "Gemini": f"{g_acc:.0f}%",
                "Ens V3": f"{v3_acc:.0f}%",
                "Ens V4": f"{v4_acc:.0f}%",
                "V4 Res": e_res_v4[:10]+".."
            })
            
    # Output Table
    df = pd.DataFrame(results)
    print("\n📊 4-Way Comparison Results (Gemini vs V3 vs V4):")
    print(df.to_markdown())
    
    # Summary Props
    avg_g = df['Gemini'].str.rstrip('%').astype(float).mean()
    avg_v3 = df['Ens V3'].str.rstrip('%').astype(float).mean()
    avg_v4 = df['Ens V4'].str.rstrip('%').astype(float).mean()
    
    print(f"\n📈 Final Accuracy Score:")
    print(f"1. Gemini Only:       {avg_g:.1f}%")
    print(f"2. Ensemble V3:       {avg_v3:.1f}% (Vision Ensemble)")
    print(f"3. Ensemble V4:       {avg_v4:.1f}% (Hybrid Vision+Text)")
    print(f"   Delta (V4-V3):     {avg_v4 - avg_v3:+.1f}%p")

if __name__ == "__main__":
    asyncio.run(evaluate())
