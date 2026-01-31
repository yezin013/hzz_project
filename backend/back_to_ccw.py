import json

def rewind_ring(ring, ensure_ccw=True):
    area = sum((p2[0] - p1[0]) * (p2[1] + p1[1]) for p1, p2 in zip(ring, ring[1:] + [ring[0]]))
    is_ccw = area < 0
    
    if ensure_ccw != is_ccw:
        return ring[::-1]
    return ring

def rewind_geometry(geometry, ensure_ccw=True):
    if geometry['type'] == 'Polygon':
        geometry['coordinates'][0] = rewind_ring(geometry['coordinates'][0], ensure_ccw)
        for i in range(1, len(geometry['coordinates'])):
            geometry['coordinates'][i] = rewind_ring(geometry['coordinates'][i], not ensure_ccw)
            
    elif geometry['type'] == 'MultiPolygon':
        for i in range(len(geometry['coordinates'])):
            geometry['coordinates'][i][0] = rewind_ring(geometry['coordinates'][i][0], ensure_ccw)
            for j in range(1, len(geometry['coordinates'][i])):
                geometry['coordinates'][i][j] = rewind_ring(geometry['coordinates'][i][j], not ensure_ccw)
    return geometry

print("Converting sig.json back to CCW...")
try:
    with open('d:/final_project/source/frontend/public/sig.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for feature in data['features']:
        feature['geometry'] = rewind_geometry(feature['geometry'], ensure_ccw=True)
        
    with open('d:/final_project/source/frontend/public/sig.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    print("Converted sig.json to CCW successfully")
except Exception as e:
    print(f"Error: {e}")
