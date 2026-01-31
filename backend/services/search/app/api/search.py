
from fastapi import APIRouter, HTTPException
from app.utils.es_client import get_es_client
from app.db.mariadb import get_liquor_details
from app.utils.search_stats import save_search_query, get_top_searches
from pydantic import BaseModel
from typing import Optional

class SearchRequest(BaseModel):
    query: str

router = APIRouter()

def search_liquor_fuzzy(text: str):
    es = get_es_client()
    if not es:
        print("❌ Elasticsearch client not available")
        return None

    # Search query: Multi-level scoring for better accuracy
    index_name = "liquor_integrated"
    
    query = {
        "query": {
            "bool": {
                "should": [
                    # 1. Exact match (highest priority)
                    {
                        "term": {
                            "name.keyword": {
                                "value": text,
                                "boost": 100.0
                            }
                        }
                    },
                    # 2. Exact match (case-insensitive, all words must match)
                    {
                        "match": {
                            "name": {
                                "query": text,
                                "operator": "and",
                                "boost": 50.0
                            }
                        }
                    },
                    # 3. Romanized match (for English OCR input like "Baekseju" → "백세주")
                    {
                        "match": {
                            "name.romanized": {
                                "query": text,
                                "operator": "or",
                                "boost": 40.0
                            }
                        }
                    },
                    # 4. Phonetic match (pronunciation-based fuzzy matching)
                    {
                        "match": {
                            "name.phonetic": {
                                "query": text,
                                "boost": 20.0
                            }
                        }
                    },
                    # 5. Fuzzy match (partial word matching with typo tolerance)
                    {
                        "match": {
                            "name": {
                                "query": text,
                                "fuzziness": "AUTO",
                                "boost": 10.0,
                                "operator": "or"
                            }
                        }
                    }
                ],
                "minimum_should_match": 1
            }
        },
        "min_score": 1.5,  # Lowered for better OCR recall
        "size": 10
    }

    try:
        response = es.search(index=index_name, body=query)
        hits = response['hits']['hits']
        
        if hits:
            best_match = hits[0]['_source']
            score = hits[0]['_score']
            
            print(f"✅ ES Match Found: '{best_match.get('name')}' (Score: {score})")
            
            # Transform ES data to Frontend 'SearchResult' interface
            source = best_match
            
            # Type mapping (approximate based on common IDs)
            type_map = {
                1: "과실주", 2: "리큐르/기타주류", 3: "약주,청주", 4: "증류주", 
                5: "탁주(고도0)", 6: "탁주(저도)", 7: "기타"
            }
            type_id = source.get('type_id')
            drink_type = type_map.get(type_id, "전통주") if type_id else "전통주"

            # Format ABV
            abv = source.get('drink_abv')
            if abv:
                try:
                    abv_float = float(abv)
                    if abv_float < 1.0:
                        abv = f"{int(abv_float * 100)}%"
                    else:
                        abv = f"{abv}%"
                except ValueError:
                    abv = f"{abv}%"

            result = {
                "id": source.get('drink_id'),
                "name": source.get('name'),
                "description": source.get('description') or source.get('intro'),
                "intro": source.get('intro'), 
                "image_url": source.get('image_url'),
                "url": source.get('url', ''),
                "tags": [], 
                "score": score,
                "province": source.get('region', {}).get('province'),
                "city": source.get('region', {}).get('city'),
                "detail": {
                    "알콜도수": f"{source.get('alcohol', 0) * 100:.1f}%",
                    "용량": source.get('volume'),
                    "종류": source.get('type'),
                    "원재료": source.get('ingredients'),
                    "수상내역": ", ".join(source.get('awards', [])) if isinstance(source.get('awards'), list) else str(source.get('awards', ''))
                },
                "brewery": {
                    "name": None, 
                    "address": source.get('region', {}).get('city'),
                    "homepage": None,
                    "contact": None
                },
                "pairing_food": source.get('foods', []), 
                "cocktails": source.get('cocktails', []), 
                "selling_shops": source.get('selling_shops', []), 
                "selling_shops": source.get('selling_shops', []), 
                "encyclopedia": source.get('description', ''),
                "taste": source.get('taste'),  # Add taste profile
                "candidates": [
                    {
                        "name": hit['_source']['name'],
                        "score": hit['_score'],
                        "image_url": hit['_source'].get('image_url', ''),
                        "id": hit['_source'].get('drink_id')
                    }
                    for hit in response['hits']['hits'][:5]
                ]
            }
            
            return result
        
        print(f"❌ No ES match found for '{text}'")
        
        # Debug: Show top candidates that didn't meet min_score
        debug_query = query.copy()
        debug_query.pop('min_score', None)  # Remove min_score to see all results
        debug_query['size'] = 5
        try:
            debug_response = es.search(index=index_name, body=debug_query)
            debug_hits = debug_response['hits']['hits']
            if debug_hits:
                print(f"🔍 Top 5 candidates (below threshold):")
                for idx, hit in enumerate(debug_hits[:5], 1):
                    print(f"  {idx}. '{hit['_source']['name']}' (Score: {hit['_score']:.2f})")
            else:
                print(f"🔍 No candidates found at all for query: '{text}'")
        except Exception as debug_e:
            print(f"⚠️ Debug query failed: {debug_e}")
        
        return None

    except Exception as e:
        print(f"❌ Search error: {e}")
        return None

class SearchRequest(BaseModel):
    query: str

@router.post("")
async def search_endpoint(request: SearchRequest):
    result = search_liquor_fuzzy(request.query)
    if not result:
        raise HTTPException(status_code=404, detail="Liquor not found")
    return result

# Weather-based recommendation weights
WEATHER_WEIGHTS = {
    "rain": {"탁주": 3, "탁주(고도0)": 3, "탁주(저도)": 3, "약주": 2, "약주,청주": 2},
    "snow": {"증류주": 3, "약주": 2, "약주,청주": 2},
    "cold": {"증류주": 3, "약주": 2, "약주,청주": 2},
    "hot": {"과실주": 3, "탁주": 2, "탁주(저도)": 2, "리큐르/기타주류": 2},
    "clear": {"약주": 2, "약주,청주": 2, "과실주": 2}
}

@router.get("/debug/region_query/{province}")
async def debug_region_query(province: str):
    """Debug endpoint to test ES region query directly."""
    es = get_es_client()
    if not es:
        return {"error": "ES not available"}
    
    # Test match query
    query = {
        "query": {"match": {"region.province": province}},
        "size": 5
    }
    
    try:
        response = es.search(index="liquor_integrated", body=query)
        hits = response['hits']['hits']
        return {
            "province": province,
            "total_hits": response['hits']['total']['value'] if isinstance(response['hits']['total'], dict) else response['hits']['total'],
            "returned_hits": len(hits),
            "samples": [{"name": h['_source'].get('name'), "region": h['_source'].get('region')} for h in hits]
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/region")
async def search_by_region(
    province: str, 
    city: Optional[str] = None, 
    season: Optional[str] = None, 
    weather_condition: Optional[str] = None,
    weather_sort: bool = False,
    size: int = 1000
):
    """
    Search drinks by region using Elasticsearch for high performance.
    Supports filtering by season (Spring, Summer, Autumn, Winter).
    Supports weather-based sorting when weather_sort=true.
    """
    print(f"🚀 [Search] Attempting Region Search via Elasticsearch (Province: {province}, City: {city})")

    es = get_es_client()
    if not es:
        print("❌ [Search] Elasticsearch client unavailable.")
        raise HTTPException(status_code=503, detail="Search service unavailable. Please try again later.")

    # Build ES Query
    # Note: 'province' and 'city' are nested in 'region' in ETL, but mapped flat?
    # Checked ETL: "region": { "province": ..., "city": ... }
    # So we need nested query or use dot notation if mapped as object?
    # Default dynamic mapping for dict is object. So 'region.province'.
    # Use 'match' for region fields (works with keyword, more flexible)
    must_conditions = [
        {"match": {"region.province": province}}
    ]
    
    if city:
        must_conditions.append({"match": {"region.city": city}})

    if season:
        # Map Korean season to English for ES
        season_map = {
            "봄": "Spring",
            "여름": "Summer",
            "가을": "Autumn",
            "겨울": "Winter"
        }
        english_season = season_map.get(season, season) # Default to original if no match (e.g. already English)
        must_conditions.append({"match": {"season": english_season}})

    print(f"DEBUG: must_conditions = {must_conditions}")

    query = {
        "query": {
            "bool": {
                "must": must_conditions
            }
        },
        "sort": [
            # Sort by name as secondary (primary done in Python)
            {"name.keyword": {"order": "asc"}}
        ],
        "size": size
    }
    
    print(f"DEBUG: Final Query = {query}")

    try:
        response = es.search(index="liquor_integrated", body=query)
        hits = response['hits']['hits']
        print(f"DEBUG: Hits found = {len(hits)}")
        
        results = []
        for hit in hits:
            source = hit['_source']
            name = source.get('name')
            
            # Dynamic Price Calculation from selling_shops
            selling_shops = source.get('selling_shops', [])
            # Fix: Handle case where lowest_price is explicitly None in ES
            lowest_price = source.get('lowest_price') or 0
            
            real_shop_prices = []
            if selling_shops:
                for shop in selling_shops:
                    # Fix: Handle case where shop['price'] is explicitly None
                    price = shop.get('price')
                    
                    # Check validity: correct price type, positive value.
                    # Relax address check: allow if address is missing but shop name exists (online shops)
                    # Safety: Filter out prices < 1000 KRW (likely data errors like size 200ml mapped to price)
                    if price and isinstance(price, (int, float)) and price >= 1000:
                        real_shop_prices.append(price)
            
            # Combine shop prices and lowest_price to find the best deal
            valid_prices = real_shop_prices
            if lowest_price and lowest_price >= 1000:
                valid_prices.append(lowest_price)
            
            if valid_prices:
                final_price = min(valid_prices)
            else:
                final_price = 0  # Fallback if no price available

            results.append({
                "id": source.get('drink_id'),
                "name": name,
                "image_url": source.get('image_url'),
                "type": source.get('type') or "전통주",
                "alcohol": f"{source.get('alcohol', 0) * 100:.0f}%",
                "price": final_price, # Use dynamically calculated price
                "volume": source.get('volume'),
                "province": source.get('region', {}).get('province'),
                "city": source.get('region', {}).get('city')
            })
        
        # Apply weather-based sorting
        if weather_sort and weather_condition:
            weights = WEATHER_WEIGHTS.get(weather_condition, {})
            for item in results:
                type_name = item.get("type", "")
                item["weather_score"] = weights.get(type_name, 1)
                # Add has_price flag for sorting priority
                item["has_price"] = 1 if (item.get("price") and item.get("price") > 0) else 0
            # Sort by: 1) has_price (desc), 2) weather_score (desc), 3) price (asc)
            results.sort(key=lambda x: (-x.get("has_price", 0), -x.get("weather_score", 1), x.get("price", 999999)))
            
        # Default Sorting (if weather_sort is False or condition missing)
        # Prioritize: 1. Has Price (lowest_price > 0), 2. Has Ref Price, 3. Lowest Price asc
        if not (weather_sort and weather_condition):
             for item in results:
                 # Check if we have selling_shops data in the source relative to this item
                 # Actually, 'results' is a list of dicts, but we don't have the original 'source' here anymore.
                 # We must fetch the 'source' again or better, extract selling_shops in the loop above (lines 269-283).
                 pass
        
        # NOTE: I will apply the fix in the loop above (lines 269-283) instead of here.
                 
             results.sort(key=lambda x: (
                 -1 if (x.get("price") and x.get("price") > 0) else 0, 
                 x.get("price") if (x.get("price") and x.get("price") > 0) else 99999999
             ))
            
        print(f"✅ [Search] Elasticsearch Region Search Successful: {len(results)} items found.")
        return results

    except Exception as e:
        print(f"❌ [Search] Elasticsearch search failed: {e}")
        # Return empty list instead of using MariaDB
        return []


@router.get("/detail/{drink_id}")
async def get_drink_detail(drink_id: int):
    """
    Get detailed information for a specific drink by ID.
    """
    es = get_es_client()
    if not es:
        raise HTTPException(status_code=500, detail="Search Engine Error")

    try:
        # Search by drink_id
        query = {
            "query": {
                "term": {
                    "drink_id": drink_id
                }
            }
        }
        
        response = es.search(index="liquor_integrated", body=query)
        hits = response['hits']['hits']
        
        if not hits:
            raise HTTPException(status_code=404, detail="Drink not found")
            
        source = hits[0]['_source']
        
        # 술 상세 정보 조회 통계 저장
        drink_name = source.get('name')
        drink_id_value = source.get('drink_id')
        if drink_name:
            await save_search_query(drink_name, drink_id=drink_id_value)
        
        # Ensure encyclopedia is always a list
        encyclopedia = source.get('encyclopedia', [])
        if not isinstance(encyclopedia, list):
            encyclopedia = []
        
        return {
            "id": source.get('drink_id'),
            "name": source.get('name'),
            "description": source.get('description') or source.get('intro', ''),
            "intro": source.get('intro'),
            "image_url": source.get('image_url'),
            "abv": f"{source.get('alcohol', 0) * 100:.0f}%",
            "volume": source.get('volume'),
            "type": source.get('type'),
            "foods": source.get('foods', []),
            "cocktails": source.get('cocktails', []),
            "encyclopedia": encyclopedia,  # Always returns a list
            "selling_shops": [s for s in source.get('selling_shops', []) if s.get('name') and s.get('address') and len(s.get('address').strip()) > 2],
            "brewery": {
                "name": source.get('brewery', {}).get('name') if source.get('brewery') else None,
                "address": source.get('brewery', {}).get('address') or source.get('region', {}).get('city'),
                "contact": source.get('brewery', {}).get('contact'),
                "homepage": source.get('brewery', {}).get('homepage')
            },
            "province": source.get('region', {}).get('province'),
            "city": source.get('region', {}).get('city'),
            "detail": {
                "알콜도수": f"{source.get('alcohol', 0)}%",
                "용량": source.get('volume'),
                "종류": source.get('type'),
                "원재료": source.get('ingredients', ''),
                "수상내역": ", ".join(source.get('awards', [])) if isinstance(source.get('awards'), list) else str(source.get('awards', ''))
            },
            # NEW: Encyclopedia price fields
            "price_is_reference": source.get('price_is_reference', False),
            "encyclopedia_price_text": source.get('encyclopedia_price_text'),
            "encyclopedia_price_text": source.get('encyclopedia_price_text'),
            "encyclopedia_url": source.get('encyclopedia_url'),
            "taste": source.get('taste')  # Add taste profile
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"❌ Detail Search Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
class SimilarSearchRequest(BaseModel):
    name: str
    exclude_id: Optional[int] = None

def search_similar_drinks(name: str, exclude_id: Optional[int] = None):
    es = get_es_client()
    if not es:
        return []

    index_name = "liquor_integrated"  # Fixed: was drink_info
    
    # Fuzzy search query
    query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "name": {  # Changed from drink_name
                                "query": name,
                                "fuzziness": "AUTO",
                                "operator": "or" # Allow partial matches for similarity
                            }
                        }
                    }
                ],
                "must_not": []
            }
        },
        "size": 6 # Fetch a few to filter
    }
    
    if exclude_id is not None:
        query["query"]["bool"]["must_not"].append({
            "term": {"drink_id": exclude_id}  # Use drink_id consistently
        })

    try:
        response = es.search(index=index_name, body=query)
        hits = response['hits']['hits']
        
        results = []
        for hit in hits:
            source = hit['_source']
            results.append({
                "id": source.get('drink_id'),  # Use drink_id from ES
                "name": source.get('name'),
                "image_url": source.get('image_url'),
                "score": hit['_score']
           })
            
        return results

    except Exception as e:
        print(f"❌ Similar Search Error: {e}")
        return []

@router.post("/similar")
async def search_similar_endpoint(request: SimilarSearchRequest):
    return search_similar_drinks(request.name, request.exclude_id)

@router.get("/list")
async def get_drink_list(
    page: int = 1, 
    size: int = 10, 
    query: Optional[str] = None, 
    sort: Optional[str] = None,
    type: Optional[str] = None,   # Comma-separated: "Takju,Yakju"
    region: Optional[str] = None,  # Comma-separated: "Seoul,Gyeonggi"
    min_abv: Optional[float] = None,
    max_abv: Optional[float] = None,
    season: Optional[str] = None # Single value: "Spring", "Summer", etc. (or mapped from Korean)
):
    print(f"🚀 [List] Attempting to fetch Drink List via Elasticsearch (Page: {page})")
    
    es = get_es_client()
    if not es:
        print("❌ [List] Elasticsearch client unavailable.")
        raise HTTPException(status_code=503, detail="Search service unavailable. Please try again later.")

    try:
        # Calculate pagination
        from_index = (page - 1) * size
        
        # Determine sort configuration
        # User Request: Prioritize items with price data (lowest_price > 0)
        # We use a script sort to put items with price first (return 0) and others later (return 1)
        price_exists_sort = {
            "_script": {
                "type": "number",
                "script": {
                    "source": "doc['lowest_price'].size() == 0 ? 1 : (doc['lowest_price'].value > 0 ? 0 : 1)",
                    "lang": "painless"
                },
                "order": "asc"
            }
        }

        sort_config = []
        if sort == 'price_asc':
            sort_config = [price_exists_sort, {"lowest_price": {"order": "asc"}}]
        elif sort == 'price_desc':
            sort_config = [price_exists_sort, {"lowest_price": {"order": "desc"}}]
        elif sort == 'alcohol_asc':
            sort_config = [price_exists_sort, {"alcohol": {"order": "asc"}}]
        elif sort == 'alcohol_desc':
            sort_config = [price_exists_sort, {"alcohol": {"order": "desc"}}]
        elif sort == 'name_asc':
            sort_config = [price_exists_sort, {"name.keyword": {"order": "asc"}}]
        else:
            # Default sort: Price existence -> Relevance (if query) or ID
            if query:
                # If searching, relevance is usually slightly more important, but user asked for price priority.
                # Let's put price priority first, then score.
                sort_config = [
                    price_exists_sort,
                    "_score"
                ]
            else:
                sort_config = [price_exists_sort, {"drink_id": {"order": "asc"}}]


        # Build query
        bool_query = {
            "must": [],
            "should": [],
            "minimum_should_match": 0
        }

        # Apply Filters
        if type:
            types = type.split("|")
            # print(f"debug: type filter: {types}")
            bool_query["must"].append({
                "terms": { "type.keyword": types } 
            })
        
        if region:
            regions = region.split("|")
            # print(f"debug: region filter: {regions}")
            bool_query["must"].append({
                "terms": { "region.province.keyword": regions }
            })

         # ABV Range Filter
        if min_abv is not None or max_abv is not None:
            range_query = {"alcohol": {}}
            if min_abv is not None:
                range_query["alcohol"]["gte"] = min_abv
            if max_abv is not None:
                range_query["alcohol"]["lte"] = max_abv
            bool_query["must"].append({"range": range_query})

        # Season Filter
        if season:
            season_map = {
                "봄": "Spring", "spring": "Spring",
                "여름": "Summer", "summer": "Summer",
                "가을": "Autumn", "autumn": "Autumn",
                "겨울": "Winter", "winter": "Winter"
            }
            target_season = season_map.get(season, season)
            bool_query["must"].append({
                "match": { "season": target_season }
            })

        if query:
            bool_query["minimum_should_match"] = 1
            bool_query["should"] = [
                            # 1. Exact name match (highest priority)
                            {
                                "term": {
                                    "name.keyword": {
                                        "value": query,
                                        "boost": 100.0
                                    }
                                }
                            },
                            # 2. Exact name match (case-insensitive, all words)
                            {
                                "match": {
                                    "name": {
                                        "query": query,
                                        "operator": "and",
                                        "boost": 50.0
                                    }
                                }
                            },
                            # 3. Fuzzy name match (partial word matching)
                            {
                                "match": {
                                    "name": {
                                        "query": query,
                                        "fuzziness": "AUTO",
                                        "boost": 10.0,
                                        "operator": "or"
                                    }
                                }
                            },
                            # 4. ngram name match
                            {
                                "match": {
                                    "name.ngram": { 
                                        "query": query,
                                        "boost": 5.0
                                    }
                                }
                            },
                            # 5. Ingredients match
                            {
                                "match": {
                                    "ingredients": {
                                        "query": query,
                                        "boost": 5.0,
                                        "operator": "and"
                                    }
                                }
                            },
                            # 6. Province match - Increased boost significantly
                            {
                                "match": {
                                    "region.province": {
                                        "query": query,
                                        "boost": 20.0
                                    }
                                }
                            },
                            # 7. City match - Increased boost significantly
                            {
                                "match": {
                                    "region.city": {
                                        "query": query,
                                        "boost": 20.0
                                    }
                                }
                            },
                            # 8. Food pairing match
                            {
                                "match": {
                                    "foods": {
                                        "query": query,
                                        "boost": 10.0,
                                        "operator": "and"
                                    }
                                }
                            },
                            # 9. Context/Story match (Intro, Description, Tags)
                            # Changed to "and" operator to avoid matching just "liquor" in "Gyeongsang-do liquor"
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": ["intro", "description", "tags"],
                                    "boost": 1.5,
                                    "operator": "and"
                                }
                            }
                        ]

        es_query = {
            "query": { "bool": bool_query },
            "from": from_index,
            "size": size,
            "sort": sort_config
        }
        
        response = es.search(index="liquor_integrated", body=es_query)
        hits = response['hits']['hits']
        total = response['hits']['total']['value'] if isinstance(response['hits']['total'], dict) else response['hits']['total']
        
        results = []
        for hit in hits:
            source = hit['_source']
            
            results.append({
                "id": source.get('drink_id'),
                "name": source.get('name'),
                "image_url": source.get('image_url'),
                "type": source.get('type') or "전통주",
                "alcohol": f"{source.get('alcohol', 0) * 100:.0f}%",
                "volume": source.get('volume'),
                "price": source.get('lowest_price', 0),
                "intro": source.get('intro', '') or source.get('description', ''),
                "pairing_foods": source.get('foods', []),
                "selling_shops": source.get('selling_shops', [])
            })
        
        print(f"✅ [List] Elasticsearch Fetch Successful: {len(results)} items.")
        return {
            "drinks": results,
            "total": total,
            "page": page,
            "size": size,
            "total_pages": (total + size - 1) // size
        }

    except Exception as e:
        print(f"❌ [List] Elasticsearch query failed: {e}")
        # Return empty result instead of failing completely
        return {
            "drinks": [],
            "total": 0,
            "page": page,
            "size": size,
            "total_pages": 0,
            "error": "검색 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        }




@router.get("/products/{drink_name}")
async def get_products_by_drink(drink_name: str):
    """
    특정 술의 판매 상품 목록 조회 (liquor.products 인덱스)
    Fallback 적용 및 데이터 정제
    1. 실제 판매처(selling_shops)가 있으면 최우선 표시 + 깨진 텍스트 필터링
    2. 없으면 지식백과 기준 가격(lowest_price) 표시
    3. 둘 다 없으면 '구매처 검색하기' 표시
    """
    import re
    
    es = get_es_client()
    if not es:
        return {"drink_name": drink_name, "products": [], "count": 0}
    
    try:
        # Search for exact drink name match
        query = {
            "query": {
                "match": {
                    "name": {
                        "query": drink_name,
                        "operator": "and"
                    }
                }
            },
            "size": 1
        }
        
        response = es.search(index="liquor_integrated", body=query)
        hits = response['hits']['hits']
        
        products = []
        
        if hits:
            source = hits[0]['_source']
            selling_shops = source.get('selling_shops', [])
            lowest_price = source.get('lowest_price', 0)
            encyclopedia_url = source.get('encyclopedia_url', '')
            image_url = source.get('image_url', '')
            
            # --- Logic Step 1: Check for Real Shops ---
            valid_shops = []
            if selling_shops:
                 for shop in selling_shops:
                    name = shop.get('name', '판매처')
                    price = shop.get('price', 0)
                    url = shop.get('url', encyclopedia_url)
                    
                    # 1-1. Strict Separation: Exclude Offline Shops (shops with valid addresses)
                    # The user explicitly stated these are separate datasets.
                    address = shop.get('address')
                    if address and len(address.strip()) > 2:
                        continue

                    # 1-2. Text Cleaning: Filter out obviously corrupted names (containing unreadable chars)
                    # Regex to find non-standard characters (allowing Hangul, English, numbers, spaces, common punctuation)
                    # If it has strange unicodes like , u00... skip or fix
                    if re.search(r'[\uFFFD]', name): # Checks for Replacement Character
                        continue
                        
                    # 1-2. Basic Validation
                    if price >= 1000:
                        valid_shops.append({
                            "name": source.get('name'),
                            "price": price,
                            "shop": name,
                            "url": url,
                            "image_url": image_url
                        })
            
            if valid_shops:
                # 1-3. Sort by Price (Ascending)
                valid_shops.sort(key=lambda x: x['price'])
                
                # If we have valid real shops, use them ONLY. Do not fall back.
                products = valid_shops
            
            # --- Logic Step 2: Fallback to Reference Price ---
            elif lowest_price >= 1000:
                naver_shopping_url = f"https://search.shopping.naver.com/search/all?query={drink_name}"
                products.append({
                    "name": source.get('name'),
                    "price": lowest_price,
                    "shop": "지식백과 기준 가격", # Label for frontend
                    "url": naver_shopping_url,
                    "image_url": image_url
                })
                
            # --- Logic Step 3: No Data - Search Placeholder ---
            else:
                 naver_shopping_url = f"https://search.shopping.naver.com/search/all?query={drink_name}"
                 products.append({
                    "name": source.get('name'),
                    "price": 0,
                    "shop": "구매처 검색하기", # Label for frontend
                    "url": naver_shopping_url,
                    "image_url": image_url
                })

        return {
            "drink_name": drink_name,
            "products": products,
            "count": len(products)
        }
    except Exception as e:
        print(f"❌ Error fetching products for {drink_name}: {e}")
        return {"drink_name": drink_name, "products": [], "count": 0}

@router.get("/debug/shops")
async def debug_selling_shops():
    """
    Debug endpoint to find ANY item that has selling_shops data.
    """
    es = get_es_client()
    if not es:
        return {"error": "No ES connection"}
    
    try:
        # Query for documents where selling_shops field exists and is not empty
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"exists": {"field": "selling_shops"}}
                    ]
                }
            },
            "size": 5
        }
        
        response = es.search(index="products_liquor", body=query)
        hits = response['hits']['hits']
        
        results = []
        for hit in hits:
            source = hit['_source']
            shops = source.get('selling_shops', [])
            # Double check in python as 'exists' might pass empty arrays depending on mapping
            if shops:
                results.append({
                    "name": source.get('name'),
                    "shops": shops
                })
        
        return {
            "count": len(results),
            "sample_data": results
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/top-searches")
async def get_top_search_ranking(limit: int = 10):
    """
    Get top N search queries from Redis stats.
    """
    try:
        results = await get_top_searches(limit)
        return {"top_searches": results}
    except Exception as e:
        print(f"❌ Error fetching top searches: {e}")
        return {"top_searches": []}
