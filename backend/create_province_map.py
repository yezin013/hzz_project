import json
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

# Province Mapping Logic (Same as frontend/backend)
PROVINCE_PREFIXES = {
    "경기도": ["11", "28", "41"], # Seoul, Incheon, Gyeonggi
    "강원도": ["42", "51"],
    "충청북도": ["43"],
    "충청남도": ["30", "44", "36"], # Daejeon, Chungnam, Sejong
    "전라북도": ["45"],
    "전라남도": ["29", "46"], # Gwangju, Jeonnam
    "경상북도": ["27", "47"], # Daegu, Gyeongbuk
    "경상남도": ["26", "31", "48"], # Busan, Ulsan, Gyeongnam
    "제주도": ["50"],
}

def create_province_map(input_path, output_path):
    print(f"Reading {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    province_features = []
    
    # Group features by province
    grouped_shapes = {prov: [] for prov in PROVINCE_PREFIXES}
    
    print("Grouping features...")
    for feature in data['features']:
        code = feature['properties']['SIG_CD']
        prefix = code[:2]
        
        found = False
        for prov, prefixes in PROVINCE_PREFIXES.items():
            if prefix in prefixes:
                # Convert GeoJSON geometry to Shapely geometry
                geom = shape(feature['geometry'])
                if not geom.is_valid:
                    geom = geom.buffer(0) # Fix invalid geometry
                grouped_shapes[prov].append(geom)
                found = True
                break
        
        if not found:
            print(f"⚠️ Unmapped code: {code}")

    print("Merging polygons...")
    for prov, shapes in grouped_shapes.items():
        if not shapes:
            continue
            
        print(f"  Merging {prov} ({len(shapes)} cities)...")
        # Merge all polygons for this province
        merged_geom = unary_union(shapes)
        
        # Create new feature
        new_feature = {
            "type": "Feature",
            "properties": {
                "name": prov,
                "code": PROVINCE_PREFIXES[prov][0] # Use first prefix as rep code
            },
            "geometry": mapping(merged_geom)
        }
        province_features.append(new_feature)

    # Save
    output_geojson = {
        "type": "FeatureCollection",
        "features": province_features
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_geojson, f, ensure_ascii=False)
        
    print(f"✅ Saved province map to {output_path}")

if __name__ == "__main__":
    create_province_map(
        r"d:\final_project\source\frontend\public\sig.json",
        r"d:\final_project\source\frontend\public\province.json"
    )
