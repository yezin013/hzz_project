"""
Brewery API endpoints for displaying random breweries.
"""

from fastapi import APIRouter
from app.utils.es_client import get_es_client
import random

router = APIRouter()


@router.get("/random")
async def get_random_breweries(limit: int = 10):
    """
    Get random breweries from Elasticsearch.
    Returns unique breweries with name and location.
    """
    es = get_es_client()
    if not es:
        return []
    
    try:
        # Search for documents with brewery data
        query = {
            "query": {
                "exists": {
                    "field": "brewery.name"
                }
            },
            "size": 100,  # Get more to ensure uniqueness after filtering
            "_source": ["brewery", "image_url", "name"]
        }
        
        response = es.search(index="liquor_integrated", body=query)
        hits = response['hits']['hits']
        
        # Extract unique breweries
        breweries_dict = {}
        for hit in hits:
            source = hit['_source']
            brewery = source.get('brewery', {})
            if brewery and brewery.get('name'):
                name = brewery.get('name')
                # Use brewery name as key to avoid duplicates
                if name not in breweries_dict:
                    # Extract region from address
                    address = brewery.get('address', '')
                    region = extract_region(address)
                    
                    breweries_dict[name] = {
                        "name": name,
                        "address": address,
                        "region": region,
                        "contact": brewery.get('contact', ''),
                        "homepage": brewery.get('homepage', ''),
                        "image_url": source.get('image_url', ''),
                        "drink_name": source.get('name', '')
                    }
        
        # Convert to list and shuffle
        breweries = list(breweries_dict.values())
        random.shuffle(breweries)
        
        # Return limited number
        return breweries[:limit]
        
    except Exception as e:
        print(f"❌ Brewery search error: {e}")
        return []


def extract_region(address: str) -> str:
    """
    Extract region (city/province) from address.
    Example: "경기도 포천시..." -> "경기 포천"
    """
    if not address:
        return "정보 없음"
    
    # Common patterns
    provinces = ['서울', '경기도', '인천', '강원도', '충청북도', '충청남도', '충북', '충남',
                 '전라북도', '전라남도', '전북', '전남', '경상북도', '경상남도', '경북', '경남',
                 '제주도', '제주', '부산', '대구', '광주', '대전', '울산', '세종']
    
    # Try to find province
    for prov in provinces:
        if prov in address:
            # Find city after province
            parts = address.split()
            for i, part in enumerate(parts):
                if prov in part and i + 1 < len(parts):
                    city = parts[i + 1].replace('시', '').replace('군', '')
                    return f"{prov.replace('도', '')} {city}"
            return prov.replace('도', '')
    
    # Fallback: return first two parts
    parts = address.split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"
    elif len(parts) == 1:
        return parts[0]
    
    return "정보 없음"
