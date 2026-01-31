import json
import re

def get_bbox(d):
    # Extract all numbers from the path string
    coords = [float(x) for x in re.findall(r'-?\d*\.?\d+', d)]
    # This is a rough approximation. SVG paths are complex (M, L, C, z, etc.)
    # But if it's mostly absolute coordinates, we might get away with just finding min/max of all numbers.
    # However, 'd' commands often use relative coordinates (lowercase m, l, etc.).
    # Let's look at the file content again.
    # The file shows "m 133.25429,127.63884 0.58,0.33 ..."
    # Lowercase 'm' means relative move. This makes it hard to just regex numbers.
    # We need a proper SVG path parser or a smarter heuristic.
    
    # Actually, let's look at the first coordinate. "m 133.25429,127.63884"
    # If the first command is 'm', it's treated as absolute 'M' (Move To).
    # Subsequent commands are relative.
    
    # Writing a full SVG path parser is overkill.
    # Let's try to find a library or use a simpler approach.
    # If I can't easily parse it, I might have to rely on the user or trial/error for viewBox.
    # BUT, looking at the data: "m 133.25429,127.63884" -> x=133, y=127.
    # "KR-42" (Gangwon) starts at "m 281.58429,0.358837".
    # "KR-49" (Jeju) starts at "m 148.84429,592.92884".
    
    # It seems the coordinates are roughly in the range 0-600.
    # Let's try to parse it properly-ish.
    pass

import re

def parse_svg_path_bbox(d):
    # Very basic parser for M/m and subsequent numbers
    # Assumes the path starts with 'm' or 'M' followed by x,y
    # And then a series of relative or absolute commands.
    # This is tricky without a library.
    
    # Let's just extract ALL numbers and see the range. 
    # If the path uses relative coordinates, the numbers will be small (deltas).
    # If absolute, they will be large.
    # The file has "m 133..., 127... 0.58, 0.33".
    # So it uses relative coordinates after the start.
    # We MUST track the current position (pen).
    
    tokens = re.findall(r'[a-zA-Z]|[-+]?\d*\.?\d+', d)
    
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')
    
    current_x, current_y = 0, 0
    
    i = 0
    while i < len(tokens):
        cmd = tokens[i]
        i += 1
        
        if cmd.lower() == 'z':
            continue
            
        # Assume pairs of coordinates follow
        # This is a simplification. H, V, A, Q, C, etc. take different num of args.
        # But looking at the file, it seems to mostly use l (line) implicitly or explicitly?
        # "m 133... 0.58,0.33 0,0 3.8,3.83 ..."
        # It seems to be just numbers after 'm'. 
        # In SVG, if a command is missing, it repeats the last command.
        # 'm' implies 'l' for subsequent pairs.
        
        # Let's assume it's all 'l' (relative line) after the initial 'm'.
        
        if cmd == 'm':
            # First pair is absolute
            x = float(tokens[i])
            y = float(tokens[i+1])
            i += 2
            current_x = x
            current_y = y
            
            min_x = min(min_x, current_x)
            max_x = max(max_x, current_x)
            min_y = min(min_y, current_y)
            max_y = max(max_y, current_y)
            
            # Subsequent pairs are relative lines
            while i < len(tokens) and not tokens[i].isalpha():
                dx = float(tokens[i])
                dy = float(tokens[i+1])
                i += 2
                current_x += dx
                current_y += dy
                min_x = min(min_x, current_x)
                max_x = max(max_x, current_x)
                min_y = min(min_y, current_y)
                max_y = max(max_y, current_y)
                
        # Handle other commands if necessary... but the file looks simple.
        
    return min_x, min_y, max_x, max_y

with open('d:/final_project/source/korea_map_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

g_min_x, g_min_y = float('inf'), float('inf')
g_max_x, g_max_y = float('-inf'), float('-inf')

for feature in data:
    x1, y1, x2, y2 = parse_svg_path_bbox(feature['d'])
    g_min_x = min(g_min_x, x1)
    g_min_y = min(g_min_y, y1)
    g_max_x = max(g_max_x, x2)
    g_max_y = max(g_max_y, y2)

print(f"BBox: {g_min_x}, {g_min_y}, {g_max_x}, {g_max_y}")
