import re

with open('/Users/apple/WorkBuddy/20260405094656/图片提取/shop_map.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 提取 stores
stores_match = re.search(r'const stores = \[(.*?)\];', html, re.DOTALL)
stores_str = stores_match.group(1)

store_pattern = re.compile(r'{id:(\d+),name:"([^"]+)",addr:"([^"]+)",region:"([^"]+)",status:"[^"]+",lat:([\d.]+),lng:([\d.]+),')
stores = []
for match in store_pattern.finditer(stores_str):
    stores.append({
        'id': match.group(1),
        'name': match.group(2),
        'addr': match.group(3),
        'region': match.group(4),
        'lat': float(match.group(5)),
        'lng': float(match.group(6))
    })

# 分别统计沙井和新桥
shajin = [s for s in stores if s['region'] == '沙井']
xinqiao = [s for s in stores if s['region'] == '新桥']

print("=== 沙井门店 ===")
for s in shajin:
    print(f"{s['id']}: {s['name'][:20]} lat={s['lat']:.4f}, lng={s['lng']:.4f}")

print("\n=== 新桥门店 ===")
for s in xinqiao:
    print(f"{s['id']}: {s['name'][:20]} lat={s['lat']:.4f}, lng={s['lng']:.4f}")

# 计算中心点
import statistics
shajin_lat_center = statistics.mean(s['lat'] for s in shajin)
shajin_lng_center = statistics.mean(s['lng'] for s in shajin)
xinqiao_lat_center = statistics.mean(s['lat'] for s in xinqiao)
xinqiao_lng_center = statistics.mean(s['lng'] for s in xinqiao)

print(f"\n=== 中心点 ===")
print(f"沙井中心: lat={shajin_lat_center:.4f}, lng={shajin_lng_center:.4f}")
print(f"新桥中心: lat={xinqiao_lat_center:.4f}, lng={xinqiao_lng_center:.4f}")

# 计算距离
import math
lat_diff = abs(shajin_lat_center - xinqiao_lat_center)
lng_diff = abs(shajin_lng_center - xinqiao_lng_center)
distance_km = math.sqrt(lat_diff**2 * 111 + lng_diff**2 * 111 * math.cos(shajin_lat_center * 3.14159/180)) * 111

print(f"\n两中心距离: {distance_km:.2f} km")

print(f"\n=== 各区域门店数量 ===")
from collections import Counter
region_counts = Counter(s['region'] for s in stores)
for region, count in sorted(region_counts.items(), key=lambda x: -x[1]):
    print(f"{region}: {count}家")