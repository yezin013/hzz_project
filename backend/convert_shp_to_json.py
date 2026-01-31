import json
try:
    import shapefile
except ImportError:
    print("Installing pyshp...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'pyshp'])
    import shapefile

# Read the shapefile
print("Reading shapefile...")
sf = shapefile.Reader('d:/final_project/source/frontend/public/sig.shp', encoding='cp949')

# Convert to GeoJSON
features = []

for shape_record in sf.shapeRecords():
    # Get geometry
    geom = shape_record.shape
    record = shape_record.record.as_dict()
    
    # Convert coordinates
    if geom.shapeType == 5:  # Polygon
        coordinates = []
        parts = list(geom.parts) + [len(geom.points)]
        
        for i in range(len(parts) - 1):
            ring = geom.points[parts[i]:parts[i+1]]
            coordinates.append(ring)
        
        geometry = {
            "type": "Polygon",
            "coordinates": coordinates
        }
    elif geom.shapeType == 15:  # PolygonZ
        coordinates = []
        parts = list(geom.parts) + [len(geom.points)]
        
        for i in range(len(parts) - 1):
            ring = geom.points[parts[i]:parts[i+1]]
            coordinates.append(ring)
        
        geometry = {
            "type": "Polygon",
            "coordinates": coordinates
        }
    else:
        print(f"Unknown shape type: {geom.shapeType}")
        continue
    
    feature = {
        "type": "Feature",
        "properties": record,
        "geometry": geometry
    }
    features.append(feature)

# Create GeoJSON
geojson = {
    "type": "FeatureCollection",
    "features": features
}

# Save
print(f"Writing {len(features)} features to sig.json...")
with open('d:/final_project/source/frontend/public/sig.json', 'w', encoding='utf-8') as f:
    json.dump(geojson, f, ensure_ascii=False)

print("Done! Created sig.json from shapefile")
print(f"Total features: {len(features)}")

# Show first feature properties as sample
if features:
    print(f"\nSample properties from first feature:")
    for key, value in features[0]['properties'].items():
        print(f"  {key}: {value}")
