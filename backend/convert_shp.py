import shapefile
import json
import os
from pyproj import CRS, Transformer

def convert_shp_to_geojson(shp_path, prj_path, output_path):
    try:
        print(f"Reading {shp_path}...")
        reader = shapefile.Reader(shp_path, encoding='cp949')
        fields = reader.fields[1:]
        field_names = [field[0] for field in fields]
        
        # Read Projection
        print(f"Reading projection from {prj_path}...")
        with open(prj_path, 'r', encoding='utf-8') as f:
            prj_wkt = f.read()
        
        # Create Transformer
        crs_src = CRS.from_wkt(prj_wkt)
        crs_dst = CRS.from_epsg(4326)
        transformer = Transformer.from_crs(crs_src, crs_dst, always_xy=True)
        print("✅ Transformer created successfully.")

        buffer = []
        
        print(f"🔄 Converting {len(reader.shapes())} shapes...")
        
        for sr in reader.shapeRecords():
            atr = dict(zip(field_names, sr.record))
            
            # Transform geometry
            shape = sr.shape
            points = shape.points
            parts = shape.parts
            
            # Transform all points
            transformed_points = []
            for x, y in points:
                lon, lat = transformer.transform(x, y)
                # Round to 4 decimal places (~11m precision) to reduce file size
                transformed_points.append([round(lon, 4), round(lat, 4)])
            
            # Reconstruct rings
            rings = []
            if not parts:
                rings.append(transformed_points)
            else:
                parts.append(len(transformed_points))
                for j in range(len(parts) - 1):
                    start = parts[j]
                    end = parts[j+1]
                    rings.append(transformed_points[start:end])
            
            geom = {
                "type": "Polygon", 
                "coordinates": rings
            }
            
            # Filter properties to reduce size
            props = {
                "SIG_CD": atr.get("SIG_CD"),
                "SIG_KOR_NM": atr.get("SIG_KOR_NM")
            }
            
            buffer.append(dict(type="Feature", geometry=geom, properties=props)) 
            
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"type": "FeatureCollection", "features": buffer}, f, ensure_ascii=False)
            
        print(f"✅ Converted and reprojected to {output_path}")
        
    except Exception as e:
        print(f"❌ Conversion Failed: {e}")

if __name__ == "__main__":
    base_dir = r"d:\final_project\source\frontend\public"
    input_file = os.path.join(base_dir, "sig.shp")
    prj_file = os.path.join(base_dir, "GRS80_UTMK.prj")
    output_file = os.path.join(base_dir, "sig.json")
    
    if not os.path.exists(input_file):
        print(f"File not found: {input_file}")
    elif not os.path.exists(prj_file):
        print(f"Projection file not found: {prj_file}")
    else:
        convert_shp_to_geojson(input_file, prj_file, output_file)
