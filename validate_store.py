#!/usr/bin/env python3
"""
门店地址验证脚本
功能：验证门店地址的精确位置和行政街道区划，确保无误
用法: python3 validate_store.py [门店ID]
"""

import requests
import json
import re
import sys

# 高德 API Key
AMAP_KEY = "988e5336ecb90a039cb2df2ec4f09da2"

def gcj02_to_wgs84(lng, lat):
    """GCJ-02 转 WGS-84（简单近似）"""
    dlat = lat - 0.0060
    dlng = lng - 0.0065
    return dlng, dlat

def geocode_address(address):
    """调用高德地理编码 API"""
    url = "https://restapi.amap.com/v3/geocode/geo"
    try:
        resp = requests.get(url, params={
            "key": AMAP_KEY,
            "address": address,
            "city": "深圳",
            "output": "JSON"
        }, timeout=10)
        data = resp.json()
        if data.get("status") == "1" and data.get("geocodes"):
            g = data["geocodes"][0]
            gcj_lng = float(g["location"].split(",")[0])
            gcj_lat = float(g["location"].split(",")[1])
            wgs_lng, wgs_lat = gcj02_to_wgs84(gcj_lng, gcj_lat)
            return {
                "lng": wgs_lng,
                "lat": wgs_lat,
                "gcj_lng": gcj_lng,
                "gcj_lat": gcj_lat,
                "province": g.get("province", ""),
                "city": g.get("city", ""),
                "district": g.get("district", ""),
                "township": g.get("township", ""),
                "formatted": g.get("formatted_address", "")
            }
    except Exception as e:
        print(f"  ⚠️ 地理编码失败: {e}")
    return None

def regeo_address(lat, lng):
    """调用高德逆地理编码 API"""
    url = "https://restapi.amap.com/v3/geocode/regeo"
    try:
        resp = requests.get(url, params={
            "key": AMAP_KEY,
            "location": f"{lng},{lat}",
            "output": "JSON"
        }, timeout=10)
        data = resp.json()
        if data.get("status") == "1":
            r = data.get("regeocode", {})
            addr = r.get("addressComponent", {})
            township_arr = addr.get("township", [])
            township = township_arr[0] if township_arr else ""
            return {
                "province": addr.get("province", ""),
                "city": addr.get("city", ""),
                "district": addr.get("district", ""),
                "township": township,
                "streetNumber": r.get("streetNumber", {}).get("street", ""),
                "formatted": r.get("formatted_address", "")
            }
    except Exception as e:
        print(f"  ⚠️ 逆地理编码失败: {e}")
    return None

# 深圳真实行政街道区划（宝安区）
STREETS = ["福永", "怀德", "白石厦", "福海", "和平", "新和", "稔田", "塘尾", "凤塘",
         "沙井", "万丰", "上星", "上寮", "壆岗", "岗胜", "东塘", "蚝一", "蚝二", "蚝三", "蚝四",
         "新桥", "道生", "创新", "潭头", "沙一", "沙二", "沙三", "沙四",
         "松岗", "东方", "花果山", "楼岗", "洪桥头", "溪头", "沙浦", "塘��涌", "燕川", "罗田",
         "凤凰", "凤凰", "塘尾", "白石下",
         "公明", "上村", "下村", "李松朗", "西田", "将石", "甲子", "新围",
         "玉塘", "长圳", "红星", "田湾", "观凹",
         "新湖", "楼村", "新羌", "圳美", "羌下",
         "燕罗", "燕川", "燕罗", "罗田", "塘下涌", "山门", "洪桥头",
         "马田", "薯田", "合水口", "根竹园", "马山头", "石家", "将围"]

def check_street(street):
    """检查街道是否属于真实行政街道"""
    # 简单检查
    for s in STREETS:
        if s in street:
            return True
    return False

def validate_store(store):
    """验证单个门店"""
    store_id = store["id"]
    name = store["name"]
    addr = store["addr"]
    current_region = store.get("region", "未知")
    current_final = store.get("final_street", "")
    current_lat = store.get("lat", 0)
    current_lng = store.get("lng", 0)
    
    print(f"\n{'='*60}")
    print(f"【门店 {store_id}】{name}")
    print(f"地址: {addr}")
    print(f"当前区域: {current_region} / {current_final}")
    print(f"当前坐标: ({current_lng}, {current_lat})")
    
    # 地理编码
    geo_result = geocode_address(addr)
    if not geo_result:
        print("  ❌ 地理编码失败")
        return None
    
    print(f"\n--- 地理编码结果 ---")
    print(f"  高德坐标: ({geo_result['gcj_lng']}, {geo_result['gcj_lat']})")
    print(f"  省份: {geo_result['province']}")
    print(f"  城市: {geo_result['city']}")
    print(f"  区县: {geo_result['district']}")
    print(f"  街道/镇: {geo_result['township']}")
    
    # 逆地理编码
    regeo_result = regeo_address(geo_result['gcj_lng'], geo_result['gcj_lat'])
    if regeo_result:
        print(f"\n--- 逆地理编码结果 ---")
        print(f"  区县: {regeo_result['district']}")
        print(f"  街道/镇: {regeo_result['township']}")
        print(f"  道路: {regeo_result['streetNumber']}")
        print(f"  详细地址: {regeo_result['formatted']}")
    
    # 关键词检测
    keywords = ["上寮", "上星", "沙井", "新桥", "福永", "松岗", "凤凰", "福海", "燕罗", "公明", "玉塘", "新湖", "马田"]
    detected = []
    for kw in keywords:
        if kw in addr:
            detected.append(kw)
    
    if detected:
        print(f"\n--- 地址关键词 ---")
        print(f"  匹配: {detected}")
    
    # 判断建议
    print(f"\n{'='*60}")
    print(f"当前区域: {current_region}")
    print(f"高德返回: {geo_result.get('township', '无')}")
    print(f"逆地理编码: {regeo_result.get('township', '无')}")
    
    return {
        "store_id": store_id,
        "name": name,
        "addr": addr,
        "current_region": current_region,
        "current_final": current_final,
        "geo_township": geo_result.get("township", ""),
        "regeo_township": regeo_result.get("township", "") if regeo_result else "",
        "keywords": detected
    }

def main():
    html_path = "shop_map.html"
    
    # 读取门店数据
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ 文件不存在: {html_path}")
        sys.exit(1)
    
    # 解析门店数据
    stores_match = re.search(r'const stores = \[(.*?)\];', content, re.DOTALL)
    if not stores_match:
        print("❌ 无法解析门店数据")
        sys.exit(1)
    
    stores_str = stores_match.group(1)
    
    # 解析每个门店对象
    store_pattern = re.compile(r'{id:(\d+),name:"([^"]+)",addr:"([^"]+)",region:"([^"]+)",status:"[^"]+",lat:([\d.]+),lng:([\d.]+),district:"[^"]+",final_street:"([^"]+)"},?')
    
    stores = []
    for match in store_pattern.finditer(stores_str):
        stores.append({
            'id': match.group(1),
            'name': match.group(2),
            'addr': match.group(3),
            'region': match.group(4),
            'lat': match.group(5),
            'lng': match.group(6),
            'final_street': match.group(7)
        })
    
    print(f"共解析 {len(stores)} 家门店")
    
    # 检查命令行参数
    target_id = None
    if len(sys.argv) > 1:
        target_id = sys.argv[1]
    
    # 验证每家门店
    if target_id:
        # 只验证指定的门店
        for store in stores:
            if store['id'] == target_id:
                validate_store(store)
                break
    else:
        # 验证所有门店
        for i, store in enumerate(stores):
            result = validate_store(store)
            
            if i < len(stores) - 1:
                cont = input("\n按回车继续（或输入 q 退出）: ")
                if cont.lower() == 'q':
                    break
    
    print(f"\n\n{'='*60}")
    print(f"验证完成")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()