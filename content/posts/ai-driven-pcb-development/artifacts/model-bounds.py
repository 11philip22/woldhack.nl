from pathlib import Path
import re

source = Path(__file__).parent / 'models/YAAJ_BluePill_PinHeaders_H_SWD_cp.wrl'
groups = {}
for shape in re.split(r'Shape\s*\{', source.read_text())[1:]:
    match = re.search(r'point\s*\[(.*?)\]', shape, re.S)
    if not match:
        continue
    values = list(map(float, re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', match[1])))
    bounds = [(round(min(values[i::3])*2.54,3), round(max(values[i::3])*2.54,3)) for i in range(3)]
    material = re.search(r'(?:material|appearance)\s+USE\s+([\w-]+)', shape)
    key = material[1] if material else '?'
    if key not in groups:
        groups[key] = bounds
        print(key, shape[-100:].strip())
    else:
        groups[key] = [(min(a[0], b[0]), max(a[1], b[1])) for a,b in zip(groups[key],bounds)]
print(groups)
