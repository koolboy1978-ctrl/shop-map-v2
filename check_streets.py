#!/usr/bin/env python3
"""
门店街道分类检测脚本
用于检测哪些门店可能被错误归类到某个街道

使用方法:
    python3 check_streets.py                 # 检测所有门店
    python3 check_streets.py --auto-fix      # 自动修正可疑门店
    python3 check_streets.py --strict        # 使用更严格的距离阈值
"""

import json
import argparse
import math
from collections import defaultdict

# 街道合理范围定义（基于深圳宝安区/光明区实际地理位置）
# 每个街道定义: [lat_min, lat_max, lng_min, lng_max, 中文名]
STREET_BOUNDS = {
    "凤凰": {
        "bounds": [22.710, 22.800, 113.870, 113.950],
        "name": "凤凰街道",
        "description": "光明区凤凰街道（塘家、将围区域）"
    },
    "松岗": {
        "bounds": [22.740, 22.820, 113.820, 113.870],
        "name": "松岗街道",
        "description": "宝安区松岗街道"
    },
    "沙井": {
        "bounds": [22.700, 22.760, 113.800, 113.860],
        "name": "沙井街道",
        "description": "宝安区沙井街道"
    },
    "新桥": {
        "bounds": [22.710, 22.760, 113.820, 113.870],
        "name": "新桥街道",
        "description": "宝安区新桥街道"
    },
    "公明": {
        "bounds": [22.760, 22.830, 113.860, 113.920],
        "name": "公明街道",
        "description": "光明区公明街道"
    },
    "马田": {
        "bounds": [22.750, 22.810, 113.850, 113.900],
        "name": "马田街道",
        "description": "光明区马田街道"
    },
    "玉塘": {
        "bounds": [22.700, 22.760, 113.880, 113.940],
        "name": "玉塘街道",
        "description": "光明区玉塘街道（玉律、田寮）"
    },
    "福永": {
        "bounds": [22.650, 22.720, 113.800, 113.860],
        "name": "福永街道",
        "description": "宝安区福永街道"
    },
    "福海": {
        "bounds": [22.690, 22.740, 113.780, 113.840],
        "name": "福海街道",
        "description": "宝安区福海街道"
    },
    "新湖": {
        "bounds": [22.770, 22.830, 113.900, 113.960],
        "name": "新湖街道",
        "description": "光明区新湖街道（圳美、羌下）"
    },
    "燕罗": {
        "bounds": [22.780, 22.860, 113.830, 113.900],
        "name": "燕罗街道",
        "description": "宝安区燕罗街道（燕川、塘下涌）"
    }
}

# 距离阈值（单位：度，约1度≈111公里）
DISTANCE_THRESHOLD = 0.05  # 约5.5公里
STRICT_THRESHOLD = 0.03   # 约3.3公里


def haversine_distance(lat1, lng1, lat2, lng2):
    """计算两点之间的距离（公里）"""
    R = 6371  # 地球半径（公里）
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def is_in_bounds(lat, lng, bounds):
    """检查坐标是否在给定范围内"""
    return (bounds[0] <= lat <= bounds[1] and bounds[2] <= lng <= bounds[3])


def find_best_street(lat, lng, threshold):
    """找到最适合的街道"""
    best_match = None
    best_distance = float('inf')

    for street, info in STREET_BOUNDS.items():
        bounds = info["bounds"]

        # 如果在边界内，优先选择
        if is_in_bounds(lat, lng, bounds):
            # 计算到中心点的距离
            center_lat = (bounds[0] + bounds[1]) / 2
            center_lng = (bounds[2] + bounds[3]) / 2
            dist = haversine_distance(lat, lng, center_lat, center_lng)
            if dist < best_distance:
                best_distance = dist
                best_match = street

    # 如果没有在边界内的街道，选择最近的
    if best_match is None:
        for street, info in STREET_BOUNDS.items():
            bounds = info["bounds"]
            center_lat = (bounds[0] + bounds[1]) / 2
            center_lng = (bounds[2] + bounds[3]) / 2
            dist = haversine_distance(lat, lng, center_lat, center_lng)
            if dist < best_distance:
                best_distance = dist
                best_match = street

    return best_match, best_distance


def check_stores(stores, threshold, verbose=False):
    """检测门店分类问题"""
    issues = []
    street_counts = defaultdict(list)

    for store in stores:
        lat = store.get('lat', 0)
        lng = store.get('lng', 0)
        current_street = store.get('final_street', '未知')
        addr = store.get('addr', '')

        # 记录当前分类
        street_counts[current_street].append(store['id'])

        # 检查是否在合理范围内
        if current_street in STREET_BOUNDS:
            bounds = STREET_BOUNDS[current_street]["bounds"]
            if not is_in_bounds(lat, lng, bounds):
                # 计算到当前街道中心的距离
                center_lat = (bounds[0] + bounds[1]) / 2
                center_lng = (bounds[2] + bounds[3]) / 2
                dist_to_current = haversine_distance(lat, lng, center_lat, center_lng)

                # 找到最佳匹配街道
                best_street, best_dist = find_best_street(lat, lng, threshold)

                issues.append({
                    'id': store['id'],
                    'name': store['name'],
                    'addr': addr,
                    'lat': lat,
                    'lng': lng,
                    'current': current_street,
                    'dist_to_current': dist_to_current,
                    'suggested': best_street,
                    'dist_to_suggested': best_dist
                })
        else:
            # 未知街道，尝试推荐
            best_street, best_dist = find_best_street(lat, lng, threshold)
            issues.append({
                'id': store['id'],
                'name': store['name'],
                'addr': addr,
                'lat': lat,
                'lng': lng,
                'current': current_street,
                'dist_to_current': None,
                'suggested': best_street,
                'dist_to_suggested': best_dist
            })

    return issues, dict(street_counts)


def print_report(issues, street_counts, threshold_km):
    """打印检测报告"""
    print("=" * 70)
    print("📍 门店街道分类检测报告")
    print("=" * 70)

    print(f"\n📊 当前门店分布（共 {sum(len(v) for v in street_counts.values())} 家）:")
    for street, ids in sorted(street_counts.items(), key=lambda x: -len(x[1])):
        print(f"   {street}: {len(ids)} 家")

    if not issues:
        print("\n✅ 所有门店分类正常！")
        return True
    else:
        print(f"\n⚠️  发现 {len(issues)} 个分类问题（阈值: {threshold_km:.1f}km）:")
        print("-" * 70)

        for issue in sorted(issues, key=lambda x: -(x['dist_to_current'] or x['dist_to_suggested'])):
            print(f"\n🔴 #{issue['id']} {issue['name']}")
            print(f"   地址: {issue['addr']}")
            print(f"   坐标: ({issue['lat']:.4f}, {issue['lng']:.4f})")
            print(f"   当前: {issue['current']}", end="")

            if issue['dist_to_current'] is not None:
                print(f" (距中心 {issue['dist_to_current']:.1f}km)", end="")
            print()

            print(f"   建议: {issue['suggested']} (距中心 {issue['dist_to_suggested']:.1f}km)")

        return False


def auto_fix_stores(stores, issues):
    """自动修正门店分类"""
    fixed = []
    for issue in issues:
        for store in stores:
            if store['id'] == issue['id']:
                old_street = store['final_street']
                store['final_street'] = issue['suggested']
                store['region'] = issue['suggested']
                fixed.append({
                    'id': issue['id'],
                    'name': issue['name'],
                    'old': old_street,
                    'new': issue['suggested']
                })
                break
    return fixed


def main():
    parser = argparse.ArgumentParser(description='检测门店街道分类问题')
    parser.add_argument('--auto-fix', action='store_true', help='自动修正可疑门店')
    parser.add_argument('--strict', action='store_true', help='使用更严格的阈值(3km)')
    parser.add_argument('--json', action='store_true', help='输出JSON格式结果')
    args = parser.parse_args()

    # 加载数据
    with open('stores.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    stores = data['stores']

    threshold = STRICT_THRESHOLD if args.strict else DISTANCE_THRESHOLD
    threshold_km = threshold * 111  # 转换为公里

    issues, street_counts = check_stores(stores, threshold)

    if args.json:
        print(json.dumps({
            'issues': issues,
            'street_counts': street_counts,
            'threshold_km': threshold_km
        }, ensure_ascii=False, indent=2))
    else:
        all_ok = print_report(issues, street_counts, threshold_km)

        if issues and args.auto_fix:
            print("\n" + "=" * 70)
            print("🔧 自动修正以下门店:")
            print("-" * 70)
            fixed = auto_fix_stores(stores, issues)
            for f in fixed:
                print(f"   #{f['id']} {f['name']}: {f['old']} → {f['new']}")

            # 保存修正后的数据
            with open('stores.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("\n✅ stores.json 已更新")

            # 重新统计
            print("\n📊 修正后分布:")
            new_counts = defaultdict(list)
            for s in stores:
                new_counts[s['final_street']].append(s['id'])
            for street, ids in sorted(new_counts.items(), key=lambda x: -len(x[1])):
                print(f"   {street}: {len(ids)} 家")

    return 0 if all_ok else 1


if __name__ == '__main__':
    exit(main())
