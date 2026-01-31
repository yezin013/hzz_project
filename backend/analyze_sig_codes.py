import json
from collections import defaultdict

with open('d:/final_project/source/frontend/public/sig.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Group by prefix
prefix_groups = defaultdict(list)

for feature in data['features']:
    code = feature['properties']['SIG_CD']
    name = feature['properties']['SIG_KOR_NM']
    prefix = code[:2]  # First 2 digits
    
    prefix_groups[prefix].append((code, name))

# Print grouped results
for prefix in sorted(prefix_groups.keys()):
    print(f"\nPrefix {prefix}:")
    print(f"  Count: {len(prefix_groups[prefix])}")
    print(f"  Sample cities: {', '.join([name for code, name in prefix_groups[prefix][:3]])}")
    
# Also check if we need to identify which province each prefix belongs to
print("\n\nAll unique prefixes:", sorted(prefix_groups.keys()))
