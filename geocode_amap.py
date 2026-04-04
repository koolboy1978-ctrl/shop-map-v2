"""
竞品门店坐标批量获取脚本
使用高德地图 Web 服务 API 自动 geocoding
API Key: 988e5336ecb90a039cb2df2ec4f09da2
免费配额: 5000次/月，37家门店绰绰有余
"""

import requests
import json
import time
import sys
import os

# ========== 配置 ==========
AMAP_KEY = '988e5336ecb90a039cb2df2ec4f09da2'
INPUT_EXCEL = '竞品店铺信息汇总.xlsx'
OUTPUT_JSON = 'geocode_amap_results.json'
CACHE_FILE = 'geocode_amap_cache.json'

# ========== 读取 Excel ==========
import openpyxl

def read_stores():
    wb = openpyxl.load_workbook(INPUT_EXCEL, data_only=True)
    ws = wb['竞品店铺信息汇总']
    stores = []
    for row in ws.iter_rows(min_row=3, values_only=True):
        if row[0] and str(row[0]).strip() and str(row[0]).isdigit():
            sid = int(row[0])
            addr = str(row[3]).strip() if row[3] else ''
            if addr and addr != 'None':
                # 清理地址格式
                addr = addr.replace('宝安区宝安区', '宝安区')
                addr = addr.replace('宝安区福安区', '宝安区')
                stores.append({
                    'id': sid,
                    'name': str(row[1]).strip() if row[1] else '',
                    'raw_addr': addr,
                    'region': str(row[9]).strip() if row[9] else '',
                    'status': str(row[10]).strip() if row[10] else '',
                })
    return stores

# ========== 加载缓存 ==========
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

# ========== 高德 Geocoding ==========
def geocode_amap(address, retries=3):
    """调用高德地图地址解析 API"""
    url = 'https://restapi.amap.com/v3/geocode/geo'
    params = {
        'key': AMAP_KEY,
        'address': address,
        'city': '深圳',
        'output': 'json',
    }

    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=15)
            data = r.json()

            if data.get('status') == '1' and data.get('count', '0') != '0':
                # 取第一个结果
                loc = data['geocodes'][0]['location']  # 格式: "lng,lat"
                lng, lat = loc.split(',')
                return {
                    'lat': float(lat),
                    'lng': float(lng),
                    'formatted': data['geocodes'][0]['formatted_address'],
                    'district': data['geocodes'][0].get('district', ''),
                    'level': data['geocodes'][0].get('level', ''),
                }
            else:
                info = data.get('info', 'unknown')
                infocode = data.get('infocode', '')
                return {'error': f"NO_RESULT: {info} (code:{infocode})", 'raw': data}
        except requests.exceptions.Timeout:
            print(f"  ⏱ 超时，重试 {attempt+1}/{retries}")
            time.sleep(2)
        except Exception as e:
            return {'error': f"EXCEPTION: {e}"}

    return {'error': 'MAX_RETRIES_EXCEEDED'}

# ========== 主程序 ==========
def main():
    stores = read_stores()
    print(f"📋 共读取 {len(stores)} 家门店\n")

    cache = load_cache()
    results = {}
    success_count = 0
    fail_count = 0

    for i, store in enumerate(stores):
        sid = store['id']
        addr = store['raw_addr']

        print(f"[{i+1}/{len(stores)}] [{sid}] {store['name']}")
        print(f"    地址: {addr}")

        # 命中缓存
        if addr in cache:
            print(f"    ✅ 缓存命中: {cache[addr]}")
            results[str(sid)] = {**store, **cache[addr]}
            if 'error' not in cache[addr]:
                success_count += 1
            else:
                fail_count += 1
            continue

        # 调用 API
        result = geocode_amap(addr)
        time.sleep(0.3)  # 避免超限

        if 'error' not in result:
            success_count += 1
            print(f"    ✅ 成功: ({result['lat']:.6f}, {result['lng']:.6f})")
            print(f"       匹配: {result['formatted']} [{result['level']}]")
        else:
            fail_count += 1
            print(f"    ❌ 失败: {result['error']}")
            # 尝试简化地址重试
            simplified = addr.replace('社区', '').replace('街道', '').replace('旁', '')
            if simplified != addr:
                print(f"    🔄 简化地址重试: {simplified}")
                result2 = geocode_amap(simplified)
                time.sleep(0.3)
                if 'error' not in result2:
                    result = result2
                    success_count += 1
                    fail_count -= 1
                    print(f"    ✅ 简化成功: ({result['lat']:.6f}, {result['lng']:.6f})")
                else:
                    print(f"    ❌ 简化也失败")

        # 存入缓存和结果
        cache[addr] = result
        results[str(sid)] = {**store, **result}
        save_cache(cache)

        print()

    # ========== 保存结果 ==========
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"✅ 完成！成功 {success_count}/{len(stores)}，失败 {fail_count}")
    print(f"💾 结果已保存: {OUTPUT_JSON}")
    print(f"💾 缓存已保存: {CACHE_FILE}")

    return results

if __name__ == '__main__':
    results = main()
