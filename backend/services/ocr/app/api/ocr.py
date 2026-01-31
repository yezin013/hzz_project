from fastapi import APIRouter, UploadFile, File, HTTPException, Form
import httpx
import os
import json
import uuid
import time
import base64
import google.generativeai as genai
import asyncio # For threading wrapper
from difflib import SequenceMatcher
from app.utils.es_client import get_es_client

# Initialize ES Client for advanced context search
try:
    es = get_es_client()
except Exception as e:
    print(f"Warning: Failed to init ES client: {e}")
    es = None

router = APIRouter()

CLOVA_OCR_API_URL = os.getenv("CLOVA_OCR_API_URL")
CLOVA_OCR_SECRET_KEY = os.getenv("CLOVA_OCR_SECRET_KEY")

#from app.utils.search_stats import save_search_query

async def process_clova_ocr(content: bytes, filename: str):
    if not CLOVA_OCR_API_URL or not CLOVA_OCR_SECRET_KEY:
        raise HTTPException(status_code=500, detail="OCR configuration missing")

    try:
        # Prepare request for Clova OCR
        request_json = {
            "images": [
                {
                    "format": filename.split(".")[-1] if "." in filename else "jpg",
                    "name": "demo",
                    "data": base64.b64encode(content).decode("utf-8")
                }
            ],
            "requestId": str(uuid.uuid4()),
            "version": "V2",
            "timestamp": int(round(time.time() * 1000))
        }

        headers = {
            "X-OCR-SECRET": CLOVA_OCR_SECRET_KEY,
            "Content-Type": "application/json"
        }

        # Enforce HTTPS
        api_url = CLOVA_OCR_API_URL
        if api_url.startswith("http://"):
            api_url = api_url.replace("http://", "https://")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                api_url,
                headers=headers,
                json=request_json
            )
            
            if response.status_code != 200:
                print(f"OCR Error: {response.text}")
                raise HTTPException(status_code=response.status_code, detail="OCR service error")

            result = response.json()
            
            # Extract text from response
            detected_text = []
            for image in result.get("images", []):
                for field in image.get("fields", []):
                    detected_text.append(field.get("inferText", ""))
            
            return {
                "success": True,
                "text": " ".join(detected_text),
                "raw_result": result
            }

    except Exception as e:
        import traceback
        print(f"Error processing Clova OCR: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Clova OCR Error: {str(e)}")

def process_gemini_ocr(content: bytes):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API Key is missing")

    try:
        # Force REST transport for Lambda compatibility (gRPC often fails in Lambda)
        genai.configure(api_key=api_key, transport='rest')
        model = genai.GenerativeModel('gemini-2.5-flash')  # Latest model for best performance
        
        # Convert bytes to a format Gemini accepts (e.g., PIL Image or direct bytes part)
        # Gemini Python SDK supports passing a dict with 'mime_type' and 'data'
        
        image_part = {
            "mime_type": "image/jpeg", # Assuming JPEG for simplicity, or detect
            "data": content
        }
        
        # Enhanced structured prompt for liquor label analysis
        prompt = """이 이미지는 한국 전통주 술병 라벨 사진입니다.
다음 정보를 정확하게 추출해주세요:

1. **제품명** (가장 중요): 술의 정식 이름 (예: "지란지교", "백세주", "안동소주")
2. 알콜올 도수 (예: "17%", "19%")
3. 용량 (예: "500ml", "750ml")
4. 종류 (예: "약주", "청주", "증류주", "과실주")
5. 지역 (예: "전라북도 순창군")

출력 형식 (JSON):
{
  "product_name": "제품명",
  "alcohol": "도수",
  "volume": "용량",
  "type": "종류",
  "brewery": "양조장/제조사 (작은 글씨, 보통 '주식회사' '도가' 등이 붙음)",
  "region": "지역"
}

**중요 지침**:
- 제품명은 라벨에서 가장 크고 눈에 띄는 텍스트입니다
- "개봉 후", "보관 방법", "경고" 같은 텍스트는 무시하세요
- 반드시 JSON 형식으로만 답변하세요
"""
        
        start_time = time.time()
        response = model.generate_content(
            [prompt, image_part],
            generation_config={
                "temperature": 0.1,  # Very low temperature for precise factual extraction
                "top_p": 0.95,
                "top_k": 40,
                "response_mime_type": "application/json"  # Force JSON output
            }
        )
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        print(f"⏱️ Gemini Smart OCR Time: {elapsed_time:.2f}s")
        
        if response.usage_metadata:
            print(f"💰 Gemini OCR Token Usage: Input={response.usage_metadata.prompt_token_count}, Output={response.usage_metadata.candidates_token_count}, Total={response.usage_metadata.total_token_count}")
            
        # Parse structured JSON response
        import json
        try:
            result_data = json.loads(response.text)
            product_name = result_data.get("product_name", "")
            brewery = result_data.get("brewery", "") # Extract brewery
            
            # Fallback: if empty, try to get any meaningful text
            if not product_name:
                product_name = result_data.get("alcohol", "") or result_data.get("type", "")
            
            print(f"📦 Gemini Extracted Data: {result_data}")
            
            return {
                "success": True,
                "text": product_name,  # Primary search query
                "structured_data": result_data,  # Full structured info
                "raw_result": {"text": response.text}
            }
        except json.JSONDecodeError as je:
            # Fallback: treat as plain text if JSON parsing fails
            print(f"⚠️ JSON parsing failed, using raw text: {je}")
            text = response.text.strip()
            return {
                "success": True,
                "text": text,
                "raw_result": {"text": text}
            }
    except Exception as e:
        import traceback
        print(f"Gemini Smart OCR Error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gemini OCR Error: {str(e)}")

@router.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    provider: str = Form("clova")
):
    """OCR API - Rate Limited: 5회/분"""
    
    # --- Helper Functions for Ensemble ---
    async def search_es_candidates(query, size=5):
        if not query or not es: return []
        try:
            res = es.search(index="liquor_integrated", body={
                "query": {"match": {"name": {"query": query, "fuzziness": "AUTO"}}},
                "size": size
            })
            return res['hits']['hits']
        except Exception as e:
            print(f"ES Search Error: {e}")
            return []

    async def run_ensemble_v3(g_data, c_text):
        """Ensemble V3 Logic: Multi-Source Search + Re-ranking"""
        g_name = g_data.get("product_name", "")
        g_brewery = g_data.get("brewery", "")
        
        print(f"🤖 Ensemble Input: G_Name='{g_name}', G_Brewery='{g_brewery}'")

        candidates_map = {} 
        
        def add_hits(hits, source_label):
            for h in hits:
                n = h['_source']['name']
                if n not in candidates_map:
                    h['origin_query'] = source_label
                    candidates_map[n] = h

        # 1. Source A: Gemini Name
        if g_name:
            hits_g = await search_es_candidates(g_name)
            add_hits(hits_g, "gemini_name")
            
        # 2. Source B: Clova Heuristic (Longest Korean Word)
        c_tokens = [w for w in c_text.split() if len(w) >= 2 and any('\u3131' <= char <= '\uD7A3' for char in w)]
        c_tokens.sort(key=len, reverse=True)
        c_best_guess = c_tokens[0] if c_tokens else ""
        if c_best_guess and c_best_guess != g_name:
            hits_c = await search_es_candidates(c_best_guess)
            add_hits(hits_c, "clova_guess")
            
        # 3. Source C: Gemini Brewery (Context Search)
        if g_brewery and es:
            try:
                res = es.search(index="liquor_integrated", body={
                    "query": {"match": {"brewery.name": {"query": g_brewery, "fuzziness": "AUTO"}}},
                    "size": 5
                })
                add_hits(res['hits']['hits'], "gemini_brewery")
            except: pass

        # Re-ranking
        best_hit = None
        max_score = -1.0
        reason = "None"
        best_doc = None
        
        for name, hit in candidates_map.items():
            source = hit['_source']
            db_name = source.get('name', '')
            db_brewery = source.get('brewery', {}).get('name', '') or ""
            
            score = 0
            
            # Name Similarity
            sim_g = SequenceMatcher(None, g_name, db_name).ratio() * 100 if g_name else 0
            sim_c = SequenceMatcher(None, c_best_guess, db_name).ratio() * 100 if c_best_guess else 0
            score += max(sim_g, sim_c)
            
            # Brewery Bonus
            brewery_match = False
            if g_brewery and db_brewery:
                if g_brewery in db_brewery or db_brewery in g_brewery:
                    score += 40
                    brewery_match = True
            
            if not brewery_match and db_brewery and len(db_brewery) > 2 and db_brewery in c_text:
                 score += 30
                 
            # Origin Bonus
            if hit.get('origin_query') == 'gemini_brewery':
                score += 15
                
            if score > max_score:
                max_score = score
                best_hit = db_name
                best_doc = source # Return full document 
                reason = f"Score {score:.0f} ({hit.get('origin_query')})"
                
        return best_doc, reason

    try:
        # Read file content
        content = await file.read()
        
        result = {}
        
        if provider == "ensemble":
            # Parallel Execution using asyncio.gather
            # Wrapper to run sync Gemini in a separate thread
            async def run_gemini():
                return await asyncio.to_thread(process_gemini_ocr, content)
            
            # Execute both in parallel
            # returns [gemini_result, clova_result]
            results = await asyncio.gather(
                run_gemini(),
                process_clova_ocr(content, file.filename),
                return_exceptions=True # Prevent one failure from crashing the other
            )
            
            g_res = results[0]
            c_res = results[1]
            
            # Error Handling for Parallel execution
            if isinstance(g_res, Exception):
                print(f"⚠️ Gemini Parallel Error: {g_res}")
                g_res = {} # Fallback empty
            
            if isinstance(c_res, Exception):
                print(f"⚠️ Clova Parallel Error: {c_res}")
                c_res = {"text": ""} # Fallback empty

            g_structured = g_res.get('structured_data', {})
            c_text = c_res.get('text', '')
            
            # 3. Run Ensemble Logic
            best_doc, method = await run_ensemble_v3(g_structured, c_text)
            
            result['success'] = True
            result['text'] = f"Ensemble Result: {best_doc['name'] if best_doc else 'None'} ({method})"
            result['raw_result'] = {"gemini": g_structured, "clova": c_text, "method": method}
            
            if best_doc:
                result['search_result'] = best_doc
                print(f"✅ Ensemble Match: {best_doc['name']}")
            else:
                print("❌ Ensemble found no candidates.")
                
            return result

        elif provider == "gemini":
            # Wrap in thread to prevent main event loop blocking
            result = await asyncio.to_thread(process_gemini_ocr, content)
        elif provider == "clova":
            result = await process_clova_ocr(content, file.filename)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")

        print(f"[{provider.upper()}] Detected Text: {result.get('text', 'No text detected')}")
        
        # [NEW] Fuzzy Search Integration
        # from app.api.search import search_liquor_fuzzy (Removed: direct import fails in microservices)
        
        async def search_liquor_rpc(query_text: str):
            search_service_url = os.getenv("SEARCH_SERVICE_URL", "https://5p1of4jt04.execute-api.ap-northeast-2.amazonaws.com/api/python/search")
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(search_service_url, json={"query": query_text})
                    if resp.status_code == 200:
                        return resp.json()
                    else:
                        print(f"⚠️ Search Service Error: {resp.status_code} - {resp.text}")
                        return None
            except Exception as ex:
                print(f"⚠️ Search RPC Failed: {ex}")
                return None

        detected_text = result.get('text', '')
        
        # Gemini Smart OCR: Use structured product_name directly
        if provider == "gemini" and 'structured_data' in result:
            structured_data = result.get('structured_data', {})
            product_name = structured_data.get('product_name', '')
            
            if product_name:
                print(f"🎯 Gemini Product Name: '{product_name}' (from structured_data)")
                search_query = product_name
                
                # Direct search with Gemini's extracted name
                search_result = await search_liquor_rpc(search_query)
                
                if search_result:
                    result['search_result'] = search_result
                    print(f"✅ ES Match Found: '{search_result.get('name')}'")
                else:
                    print(f"⚠️ No match for '{search_query}', trying fallback...")
                    # Fallback: try without trailing words like "막걸리", "소주"
                    words = product_name.split()
                    if len(words) > 1:
                        # Try first word only (e.g., "희양산" from "희양산 막걸리")
                        fallback_query = words[0]
                        print(f"🔄 Fallback Query: '{fallback_query}'")
                        search_result = await search_liquor_rpc(fallback_query)
                        
                        if search_result:
                            result['search_result'] = search_result
                            print(f"✅ ES Match Found (fallback): '{search_result.get('name')}'")
                        else:
                            print("❌ No match found even with fallback")
                
                return result
            else:
                print("⚠️ Gemini returned empty product_name, trying text extraction...")
        
        # Clova OCR or Gemini fallback: Use text extraction logic
        if detected_text:
            import re
            
            # Blocklist to filter out instructional/warning text
            blocklist = [
                "개봉", "보관", "반품", "유통기한", "경고", "지나친", "음주", "청소년", "임신", 
                "원재료", "업소명", "소재지", "내용량", "식품유형", "고객", "상담", "신고", 
                "불량식품", "뚜껑", "취급", "교환", "환불", "소비자", "분쟁", "해결", "기준", "의거",
                "100%", "증류식"
            ]
            
            # Split into lines
            lines = [line.strip() for line in detected_text.split('\n') if line.strip()]
            
            # Strategy 1: Find Korean product names (usually 2-6 characters)
            # Look for patterns like "안동소주", "백세주", "이화주" etc.
            product_name_candidates = []
            
            for line in lines:
                if any(keyword in line for keyword in blocklist): continue
                if re.search(r'\d+%|\d+ml|alc\.|vol\.', line, re.IGNORECASE): continue
                korean_phrases = re.findall(r'[가-힣]{2,10}', line)
                english_words = re.findall(r'\b[a-zA-Z]{3,15}\b', line)
                
                for phrase in korean_phrases:
                    if phrase in ["막걸리", "약주", "청주", "과실주", "리큐르"]: continue
                    if any(region in phrase for region in ["안동", "경주", "문배", "진주", "이강", "양촌", "서울"]):
                        product_name_candidates.insert(0, phrase)
                    else:
                        product_name_candidates.append(phrase)
                        
                for word in english_words:
                    if word.lower() in ['the', 'and', 'for', 'with', 'alcohol', 'traditional', 'korean', 'rice', 'wine', 'beer', 'spirits']: continue
                    product_name_candidates.append(word)
            
            if not product_name_candidates:
                for line in lines:
                    if re.search(r'[가-힣]', line):
                        if not any(keyword in line for keyword in blocklist):
                            korean_only = re.sub(r'[^가-힣\s]', '', line).strip()
                            if korean_only and len(korean_only) >= 2:
                                product_name_candidates.append(korean_only)
                                break
            
            if product_name_candidates:
                # Deduplicate and prioritize longer strings (e.g., "지란지교" over "지란")
                seen = set()
                unique_candidates = []
                for candidate in product_name_candidates:
                    normalized = candidate.strip()
                    if normalized and normalized not in seen:
                        seen.add(normalized)
                        unique_candidates.append(normalized)
                
                # Sort by length (longest first) to prefer "지란지교" over "지란"
                unique_candidates.sort(key=len, reverse=True)
                search_query = unique_candidates[0]
                print(f"🔍 OCR Candidates (deduped): {unique_candidates[:5]}")
            elif lines:
                valid_lines = [line for line in lines if not any(keyword in line for keyword in blocklist)]
                search_query = valid_lines[0] if valid_lines else lines[0]
            else:
                search_query = detected_text[:20]

            print(f"🔍 Search Query: '{search_query}'")
            
            # CALL CHANGED HERE
            search_result = await search_liquor_rpc(search_query) 
            
            # Romanization Logic
            if not search_result and re.match(r'^[a-zA-Z0-9\s\.,]+$', search_query):
                custom_romanization = {
                    "geisha": "게이샤", "baekseju": "백세주", "makgeolli": "막걸리",
                    "hwayo": "화요", "andong": "안동", "gyeongju": "경주",
                    "chamisul": "참이슬", "jinro": "진로", "bokbunja": "복분자",
                    "soju": "소주", "yakju": "약주", "cheongju": "청주",
                }
                query_lower = search_query.lower().strip()
                if query_lower in custom_romanization:
                    hangul_query = custom_romanization[query_lower]
                    print(f"🗺️ Custom Mapping: '{search_query}' -> '{hangul_query}'")
                    search_result = await search_liquor_rpc(hangul_query) # CALL CHANGED
                
                if not search_result:
                    try:
                        from hangulize import hangulize
                        for lang in ['jpn', 'eng', 'ita']:
                            try:
                                hangul_query = hangulize(search_query, lang)
                                search_result = await search_liquor_rpc(hangul_query) # CALL CHANGED
                                if search_result: break
                            except: continue
                    except Exception as e:
                        print(f"⚠️ Hangulize Error: {e}")

            if search_result:
                result['search_result'] = search_result
                print(f"✅ ES Match Found: '{search_result.get('name')}'")
                # Log stats (Optional: Skipping RPC for stats to avoid complexity, or fire-and-forget)
                # For now just print log
                print(f"📊 Search identified: {search_result.get('name')}")
            else:
                print("  -> No matching liquor found in DB")

        return result

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"General Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
