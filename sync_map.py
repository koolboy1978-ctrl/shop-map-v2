#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
竞品门店地图 - 自动同步脚本（含版本管理）
功能：
    1. 从 Excel 表格读取门店数据，自动生成 stores.json 和地图
    2. 每次同步自动创建版本快照，可随时回退到任意版本
    3. 支持 --rollback 参数回退到指定版本

使用方法：
    python sync_map.py                    # 同步并创建新版本
    python sync_map.py --rollback v3       # 回退到 v3 版本
    python sync_map.py --list              # 查看所有版本
    python sync_map.py --current           # 查看当前版本

版本目录结构：
    versions/
    ├── changelog.json       ← 版本记录清单
    ├── v1/
    │   ├── stores.json
    │   └── shop_map.html
    ├── v2/
    │   ├── stores.json
    │   └── shop_map.html
    └── v3/
        ├── stores.json
        └── shop_map.html
"""

import os
import sys
import json
import time
import shutil
import argparse

# ============================================================
# 配置
# ============================================================
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
VERSIONS_DIR = os.path.join(SCRIPT_DIR, "versions")
CHANGELOG_FILE = os.path.join(VERSIONS_DIR, "changelog.json")
EXCEL_FILE  = os.path.join(SCRIPT_DIR, "竞品店铺信息汇总.xlsx")
AMAP_KEY    = "988e5336ecb90a039cb2df2ec4f09da2"
STORES_JSON = os.path.join(SCRIPT_DIR, "stores.json")
CURRENT_HTML = os.path.join(SCRIPT_DIR, "shop_map.html")
LOG_FILE   = os.path.join(SCRIPT_DIR, "sync_log.txt")


# ============================================================
# 工具函数
# ============================================================
def log(msg):
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")


def banner():
    print("=" * 54)
    print("🗺️  竞品地图同步工具  v2.0（含版本管理）")
    print("=" * 54)


def ensure_dirs():
    """确保必要目录存在"""
    os.makedirs(VERSIONS_DIR, exist_ok=True)


def load_changelog():
    """加载版本记录"""
    if os.path.exists(CHANGELOG_FILE):
        with open(CHANGELOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"current": None, "versions": []}


def save_changelog(data):
    """保存版本记录"""
    with open(CHANGELOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def next_version(changelog):
    """生成下一个版本号"""
    if not changelog["versions"]:
        return "v1"
    last = changelog["versions"][-1]["version"]
    # 支持 v1, v2 ... v99
    num = int(last.replace("v", ""))
    return f"v{num + 1}"


def list_versions():
    """列出所有版本"""
    changelog = load_changelog()
    banner()
    print(f"\n📦 当前版本：{changelog['current'] or '无'}\n")
    print(f"{'版本号':<8} {'日期时间':<20} {'门店数':<8} {'说明'}")
    print("-" * 60)
    if not changelog["versions"]:
        print("  暂无版本记录\n")
    for v in changelog["versions"]:
        current_mark = " ◀ 当前" if v["version"] == changelog["current"] else ""
        print(f"  {v['version']:<6} {v['created']:<20} {v['store_count']:<8} {v.get('note', '')}{current_mark}")
    print()


def show_current():
    """显示当前版本信息"""
    changelog = load_changelog()
    banner()
    if not changelog["current"]:
        print("\n⚠️  尚未创建任何版本，请先运行同步：python sync_map.py\n")
        return
    v = next((x for x in changelog["versions"] if x["version"] == changelog["current"]), None)
    if v:
        print(f"\n✅ 当前版本：{v['version']}")
        print(f"   创建时间：{v['created']}")
        print(f"   门店数量：{v['store_count']} 家")
        print(f"   说明：{v.get('note', '（无）')}")
        print(f"   文件路径：versions/{v['version']}/")
    print()


# ============================================================
# 版本快照
# ============================================================
def create_snapshot(version, stores, note=""):
    """为当前数据创建版本快照"""
    ensure_dirs()
    changelog = load_changelog()

    version_dir = os.path.join(VERSIONS_DIR, version)
    os.makedirs(version_dir, exist_ok=True)

    # 复制 stores.json
    if os.path.exists(STORES_JSON):
        shutil.copy2(STORES_JSON, os.path.join(version_dir, "stores.json"))

    # 复制 shop_map.html
    if os.path.exists(CURRENT_HTML):
        shutil.copy2(CURRENT_HTML, os.path.join(version_dir, "shop_map.html"))

    # 记录到 changelog
    entry = {
        "version":    version,
        "created":    time.strftime("%Y-%m-%d %H:%M:%S"),
        "store_count": len(stores),
        "note":       note or changelog.get("last_note", ""),
    }

    # 如果当前版本不是最新，追加新版本（保持历史）
    changelog["versions"] = [v for v in changelog["versions"] if v["version"] != version]
    changelog["versions"].append(entry)
    changelog["current"] = version
    save_changelog(changelog)

    return version_dir


def rollback_to(target_version):
    """回退到指定版本"""
    changelog = load_changelog()
    version_dir = os.path.join(VERSIONS_DIR, target_version)

    if not os.path.exists(version_dir):
        print(f"❌ 版本 {target_version} 不存在！")
        list_versions()
        return False

    # 恢复 stores.json
    src_stores = os.path.join(version_dir, "stores.json")
    if os.path.exists(src_stores):
        shutil.copy2(src_stores, STORES_JSON)
        log(f"✅ 已恢复 stores.json ← versions/{target_version}/stores.json")

    # 恢复 shop_map.html
    src_html = os.path.join(version_dir, "shop_map.html")
    if os.path.exists(src_html):
        shutil.copy2(src_html, CURRENT_HTML)
        log(f"✅ 已恢复 shop_map.html ← versions/{target_version}/shop_map.html")

    # 更新当前版本标记
    changelog["current"] = target_version
    save_changelog(changelog)

    print(f"\n✅ 已回退到版本 {target_version}")
    print(f"   请用浏览器打开 shop_map.html 查看\n")
    return True


# ============================================================
# 地理编码 + 逆地理编码
# ============================================================
def gcj02_to_wgs84(lng, lat):
    """GCJ-02 转 WGS-84"""
    a  = 6378245.0
    ee = 0.00669342162296594323
    d_lat = _t_lat(lng - 105.0, lat - 35.0)
    d_lng = _t_lng(lng - 105.0, lat - 35.0)
    rad_lat = lat / 180.0 * 3.14159265358979
    magic   = 1 - ee * (rad_lat * rad_lat) / 2.0
    d_lat   = (d_lat * 180.0) / (a / magic * (3.14159265358979 * rad_lat) / 2.0 * rad_lat)
    d_lng   = (d_lng * 180.0) / (a / magic * 3.14159265358979 * rad_lat / 2.0 * rad_lat)
    return lng - d_lng / 3600.0, lat - d_lat / 3600.0


def regeo_address(gcj_lng, gcj_lat, retries=3):
    """调用高德逆地理编码 API，获取精确行政区划（街道级别）"""
    import requests
    url = "https://restapi.amap.com/v3/geocode/regeo"
    for attempt in range(retries):
        try:
            resp = requests.get(url, params={
                "key": AMAP_KEY,
                "location": f"{gcj_lng},{gcj_lat}",
                "extensions": "base",
                "output": "JSON"
            }, timeout=10)
            data = resp.json()
            if data.get("status") == "1" and data.get("regeocode"):
                rg = data["regeocode"]
                address = rg.get("addressComponent", {})
                
                # 获取各级行政区划
                province = address.get("province", "")  # 广东省
                city = address.get("city", "")           # 深圳市
                district = address.get("district", "")   # 宝安区/光明区
                township = address.get("township", "")   # 街道/镇（如：沙井街道、福永街道）
                neighborhood = address.get("neighborhood", "")
                building = address.get("building", "")
                
                # 清洗 township（去掉"街道"、"镇"等后缀）
                clean_township = township.replace("街道", "").replace("镇", "").replace("管理处", "")
                
                return {
                    "province": province,
                    "city": city,
                    "district": district,           # 区县：宝安区/光明区
                    "township": clean_township,       # 街道：沙井/福永/松岗
                    "township_raw": township,         # 原始：沙井街道
                    "full_address": rg.get("formatted_address", ""),
                    "business_area": address.get("businessAreas", []),
                }
            elif data.get("info") == "EMAIL_AIO_LIMIT":
                log(f"  ⚠️ 高德 API 频率限制，等待 2 秒后重试…")
                time.sleep(2)
            else:
                log(f"  ⚠️ 逆地理编码失败")
                return None
        except Exception as e:
            log(f"  ⚠️ 网络错误：{e}，重试中…")
            time.sleep(2)
    return None


def _t_lat(x, y):
    ret = -100.0 + 2.0*x + 3.0*y + 0.2*y*y + 0.1*x*y + 0.2*((x**2)**0.5)
    ret += (20.0*((3.0*x*abs(x))**0.5)) / 16.0
    ret += (20.0*(abs(y))**0.5) / 3.0
    ret += (40.0*abs(y)) / 3.0
    ret += (19.3*((x**2)**0.5)) / 16.0
    ret += (88.0*abs(x)) / 180.0
    ret += (2.0*abs(x)**2) / 5.0
    ret += (18.0*abs(y)) / 20.0
    ret += (15.0*abs(y)**2) / 7.0
    ret += (46.0*abs(y)**2) / 3.0
    ret += (38.0*abs(y)) / 7.0
    ret += (250.0*abs(y)) / 3.0
    return ret


def _t_lng(x, y):
    ret = 300.0 + x + 2.0*y + 0.1*x*x + 0.1*x*y + 0.1*((x**2 + y**2)**0.5)
    ret += (20.0*((3.0*x*abs(x))**0.5)) / 16.0
    ret += (20.0*(abs(y))**0.5) / 3.0
    ret += (40.0*abs(y)) / 3.0
    ret += (19.3*((x**2)**0.5)) / 16.0
    ret += (85.0*abs(x)) / 180.0
    ret += (3.0*abs(x)**2) / 5.0
    ret += (47.0*abs(y)) / 7.0
    ret += (28.0*abs(y)) / 20.0
    ret += (23.0*abs(y)**2) / 5.0
    ret += (39.0*abs(y)**2) / 4.0
    ret += (35.0*abs(y)) / 2.0
    ret += (260.0*abs(y)) / 3.0
    return ret


# ============================================================
# 区域标准化映射（街道级别）
# ============================================================
STREET_MAPPING = {
    # 沙井片区
    "沙井": "沙井",
    "新桥": "新桥",
    "壆岗": "沙井",
    "步涌": "沙井",
    "后亭": "沙井",
    "蚝乡": "沙井",
    "万丰": "沙井",
    "上星": "沙井",
    "上南": "沙井",
    "共和": "沙井",
    "沙二": "沙井",
    "沙三": "沙井",
    # 松岗片区
    "松岗": "松岗",
    "燕川": "燕罗",
    "塘下涌": "松岗",
    "罗田": "燕罗",
    "楼岗": "松岗",
    "松瑞": "松岗",
    "红腾": "松岗",
    "立业": "松岗",
    # 公明片区
    "公明": "公明",
    "上村": "公明",
    "李松蓢": "公明",
    "下村": "公明",
    "薯田埔": "公明",
    "合水口": "公明",
    "马园": "公明",
    # 光明片区
    "光明": "光明",
    "凤凰": "凤凰",
    "塘家": "凤凰",
    "东周": "凤凰",
    "长圳": "光明",
    # 玉塘街道（玉律、田寮属于玉塘）
    "玉律": "玉塘",
    "田寮": "玉塘",
    "玉塘": "玉塘",
    "马田": "马田",
    # 福永片区
    "福永": "福永",
    "白石厦": "福永",
    "桥头": "福永",
    "怀德": "福永",
    # 福海片区
    "福海": "福海",
    "和平": "福海",
    "新和": "福海",
    "稔田": "福海",
    "塘尾": "福海",
    "凤塘": "福海",
    # 石岩片区
    "石岩": "石岩",
    "官田": "石岩",
    "浪心": "石岩",
    # 新湖片区（公明新湖）
    "新湖": "新湖",
    "圳美": "新湖",
    "羌下": "新湖",
    # 潭头（属于福海）
    "潭头": "福海",
    # 上寮/上星（属于新桥街道，2016年从沙井析出）
    "上寮": "新桥",
    "上星": "新桥",
    # 燕罗（高德返回的街道名，属于燕川/松岗片区）
    "燕罗": "燕罗",
    # 岗胜路（沙井片区）
    "岗胜": "沙井",
    "红湖": "燕罗",
    "蚝涌": "松岗",
}


def normalize_street(township, address=""):
    """
    混合方式确定街道（优先级：关键词匹配 > 高德API）：
    1. 优先使用地址关键词匹配（更可靠）
    2. 其次使用高德 API 返回的 township
    3. 如果都没有，返回"其他"
    """
    # 方式1：优先用地址关键词匹配（更可靠）
    if address:
        for keyword, street in STREET_MAPPING.items():
            if keyword in address:
                return street
    
    # 方式2：使用高德 API 返回的街道
    if township:
        # 清洗后缀
        clean = township.replace("街道", "").replace("镇", "").replace("管理处", "")
        if clean in STREET_MAPPING:
            return STREET_MAPPING[clean]
        # 如果在映射表里找不到，也直接返回
        if clean:
            return clean
    
    # 默认
    return "其他"


def geocode_address(address, retries=3):
    """调用高德地理编码 API"""
    import requests
    url = "https://restapi.amap.com/v3/geocode/geo"
    for attempt in range(retries):
        try:
            resp = requests.get(url, params={
                "key": AMAP_KEY, "address": address,
                "city": "深圳", "output": "JSON"
            }, timeout=10)
            data = resp.json()
            if data.get("status") == "1" and data.get("geocodes"):
                g = data["geocodes"][0]
                gcj_lng = float(g["location"].split(",")[0])
                gcj_lat = float(g["location"].split(",")[1])
                wgs_lng, wgs_lat = gcj02_to_wgs84(gcj_lng, gcj_lat)
                
                # 顺便调用逆地理编码，获取精确街道
                regeo_result = regeo_address(gcj_lng, gcj_lat)
                street_info = {}
                if regeo_result:
                    # 使用混合方式确定街道
                    final_street = normalize_street(
                        regeo_result.get("township", ""),
                        address
                    )
                    street_info = {
                        "district": regeo_result.get("district", ""),
                        "township": regeo_result.get("township", ""),
                        "province": regeo_result.get("province", ""),
                        "city": regeo_result.get("city", ""),
                        "final_street": final_street,  # 标准化后的街道
                        "full_address": regeo_result.get("full_address", ""),
                    }
                
                return {
                    "lat": round(wgs_lat, 6), "lng": round(wgs_lng, 6),
                    "formatted": g.get("formatted_address", ""),
                    "district": g.get("district", ""),
                    **street_info,
                }
            elif data.get("info") == "EMAIL_AIO_LIMIT":
                log(f"  ⚠️ 高德 API 频率限制，等待 2 秒后重试…")
                time.sleep(2)
            else:
                log(f"  ⚠️ 地址未找到：{address}")
                return None
        except Exception as e:
            log(f"  ⚠️ 网络错误：{e}，重试中…")
            time.sleep(2)
    return None


def read_excel():
    """从 Excel 读取门店数据"""
    try:
        import openpyxl
        import pandas as pd
    except ImportError:
        log("❌ 请先安装依赖：pip install openpyxl pandas requests")
        return []

    if not os.path.exists(EXCEL_FILE):
        log(f"❌ 找不到 Excel 文件：{EXCEL_FILE}")
        return []

    df = pd.read_excel(EXCEL_FILE, header=1)
    log(f"📋 列名：{list(df.columns)[:12]}")

    def find_col(*names):
        for n in names:
            for c in df.columns:
                if n in str(c):
                    return c
        return None

    col_id     = find_col("序号")
    col_name   = find_col("店铺名称", "店名", "门店名称", "名称")
    col_addr   = find_col("地址")
    col_region = find_col("所在区域", "区域")
    col_status = find_col("营业状态", "状态")

    missing = []
    if not col_id:   missing.append("序号")
    if not col_name: missing.append("店铺名称")
    if not col_addr: missing.append("地址")
    if missing:
        log(f"❌ 缺少关键列：{missing}")
        return []

    stores = []
    for _, row in df.iterrows():
        name = str(row[col_name]).strip() if pd.notna(row[col_name]) else ""
        if not name or name == "nan":
            continue
        sid = str(int(row[col_id])) if pd.notna(row[col_id]) and str(row[col_id]).replace('.', '').isdigit() else str(len(stores) + 1)
        stores.append({
            "id":     int(sid),
            "name":   name,
            "addr":   str(row[col_addr]).strip() if pd.notna(row[col_addr]) else "",
            "region": str(row[col_region]).strip() if col_region and pd.notna(row[col_region]) else "其他",  # Excel原始区域
            "status": str(row[col_status]).strip() if col_status and pd.notna(row[col_status]) else "未知",
            "lat": None, "lng": None,
            "final_street": None,  # 标准化后的街道（稍后通过 API 确定）
        })

    log(f"✅ 共读取 {len(stores)} 家门店")
    return stores


# ============================================================
# 主同步流程
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="竞品地图同步工具", add_help=False)
    parser.add_argument("--list",    action="store_true", help="列出所有版本")
    parser.add_argument("--current", action="store_true", help="显示当前版本")
    parser.add_argument("--rollback", metavar="VERSION", help="回退到指定版本（如 --rollback v2）")
    parser.add_argument("--note",    metavar="TEXT",    help="本次更新的备注说明")
    parser.add_argument("--skip-snapshot", action="store_true", help="跳过版本快照（仅更新数据）")
    args = parser.parse_args()

    # 处理命令
    if args.list:
        list_versions()
        return
    if args.current:
        show_current()
        return
    if args.rollback:
        banner()
        rollback_to(args.rollback)
        return

    # ---------- 同步流程 ----------
    banner()
    ensure_dirs()
    changelog = load_changelog()

    stores = read_excel()
    if not stores:
        return

    # 加载已有坐标缓存（包括 final_street）
    existing_coords = {}
    if os.path.exists(STORES_JSON):
        with open(STORES_JSON, "r", encoding="utf-8") as f:
            old_data = json.load(f)
            for s in old_data.get("stores", []):
                key = f"{s['name']}|{s['addr']}"
                if s.get("lat") and s.get("lng"):
                    existing_coords[key] = {
                        "lat": s["lat"], "lng": s["lng"],
                        "formatted": s.get("formatted", ""),
                        "district": s.get("district", ""),
                        "township": s.get("township", ""),
                        "final_street": s.get("final_street", ""),
                    }

    # 获取坐标 + 逆地理编码（确定街道）
    new_count = 0
    for store in stores:
        key = f"{store['name']}|{store['addr']}"
        if key in existing_coords and existing_coords[key].get("lat"):
            store.update(existing_coords[key])
            # 如果缓存数据没有 final_street，需要重新计算
            if not store.get("final_street"):
                store["final_street"] = normalize_street(store.get("township", ""), store.get("addr", ""))
            street_src = "缓存+补全"
            log(f"  ✓ [{store['id']:2d}] {store['name'][:20]:20s}  → {store.get('final_street', '其他')}")
        elif store["addr"]:
            log(f"  🔄 [{store['id']:2d}] {store['name'][:20]:20s}  → 获取坐标中…")
            result = geocode_address(store["addr"])
            if result:
                store.update(result)
                new_count += 1
                street_src = "API" if store.get("final_street") else "地址匹配"
                log(f"  ✓ [{store['id']:2d}] {store['name'][:20]:20s}  → {store.get('final_street', '其他')}")
            else:
                store["final_street"] = normalize_street("", store["addr"])
                street_src = "地址匹配"
                log(f"  ⚠️ [{store['id']:2d}] {store['name'][:20]:20s}  → {store.get('final_street', '其他')}")
            time.sleep(0.5)  # API 调用间隔
        else:
            store["final_street"] = "其他"
            log(f"  ⚠️ 无地址：{store['name']}")

    # 确保每个门店都有 final_street
    for store in stores:
        if not store.get("final_street"):
            store["final_street"] = normalize_street(store.get("township", ""), store.get("addr", ""))
    
    # 统计各街道门店数
    street_counts = {}
    for store in stores:
        street = store.get("final_street", "其他")
        street_counts[street] = street_counts.get(street, 0) + 1
    
    log(f"📊 街道分布：{dict(sorted(street_counts.items(), key=lambda x: -x[1]))}")
    
    # 写 stores.json
    output = {
        "version":   "1.0",
        "generated": time.strftime("%Y-%m-%d"),
        "title":     "食为先·竞品门店分布地图",
        "total":     len(stores),
        "street_distribution": street_counts,
        "stores":    stores
    }
    with open(STORES_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    log(f"✅ stores.json 已更新（{len(stores)} 家，新增 {new_count} 条坐标）")

    # 生成/更新地图 HTML
    stores_json_str = json.dumps(stores, ensure_ascii=False)
    generate_map_html(stores_json_str)
    log(f"✅ shop_map.html 已更新")

    # 创建版本快照（跳过 if 指定了 --skip-snapshot）
    if not args.skip_snapshot:
        version = next_version(changelog)
        note = args.note if args.note else ""
        version_dir = create_snapshot(version, stores, note)
        log(f"✅ 版本快照已创建：{version}")
        print(f"\n📦 版本 {version} 创建完成！")
    else:
        print(f"\n⏭️  已跳过版本快照（--skip-snapshot）")

    # 打印结果摘要
    print()
    print(f"  📄 数据文件：{STORES_JSON}")
    print(f"  🌐 地图文件：{CURRENT_HTML}")
    print(f"  📦 版本记录：versions/changelog.json")
    print()
    print("  💡 常用命令：")
    print("     python sync_map.py --list       ← 查看所有版本")
    print("     python sync_map.py --current    ← 查看当前版本")
    print("     python sync_map.py --rollback v1 ← 回退到 v1")
    print()
    print("  ☁️  部署到云端：将 shop_map.html + stores.json 上传到同一目录即可")

    # 自动运行街道分类检测
    print()
    check_street_classification()


# ============================================================
# 门店街道分类检测（每次同步后自动运行）
# ============================================================
import math
from collections import defaultdict

# 街道合理范围定义
STREET_BOUNDS = {
    "凤凰": {"bounds": [22.710, 22.800, 113.870, 113.950], "name": "凤凰街道"},
    "松岗": {"bounds": [22.740, 22.820, 113.820, 113.870], "name": "松岗街道"},
    "沙井": {"bounds": [22.700, 22.760, 113.800, 113.860], "name": "沙井街道"},
    "新桥": {"bounds": [22.710, 22.760, 113.820, 113.870], "name": "新桥街道"},
    "公明": {"bounds": [22.760, 22.830, 113.860, 113.920], "name": "公明街道"},
    "马田": {"bounds": [22.750, 22.810, 113.850, 113.900], "name": "马田街道"},
    "玉塘": {"bounds": [22.700, 22.760, 113.880, 113.940], "name": "玉塘街道"},
    "福永": {"bounds": [22.650, 22.720, 113.800, 113.860], "name": "福永街道"},
    "福海": {"bounds": [22.690, 22.740, 113.780, 113.840], "name": "福海街道"},
    "新湖": {"bounds": [22.770, 22.830, 113.900, 113.960], "name": "新湖街道"},
    "燕罗": {"bounds": [22.780, 22.860, 113.830, 113.900], "name": "燕罗街道"},
}

DISTANCE_THRESHOLD = 0.05  # 约5.5公里


def haversine_distance(lat1, lng1, lat2, lng2):
    """计算两点之间的距离（公里）"""
    R = 6371
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def is_in_bounds(lat, lng, bounds):
    return bounds[0] <= lat <= bounds[1] and bounds[2] <= lng <= bounds[3]


def find_best_street(lat, lng):
    """找到最适合的街道"""
    best_match = None
    best_distance = float('inf')

    for street, info in STREET_BOUNDS.items():
        bounds = info["bounds"]
        if is_in_bounds(lat, lng, bounds):
            center_lat = (bounds[0] + bounds[1]) / 2
            center_lng = (bounds[2] + bounds[3]) / 2
            dist = haversine_distance(lat, lng, center_lat, center_lng)
            if dist < best_distance:
                best_distance = dist
                best_match = street

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


def check_street_classification():
    """检测并修正门店街道分类问题"""
    try:
        with open(STORES_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
        stores = data['stores']
    except Exception as e:
        print(f"⚠️  无法读取门店数据: {e}")
        return

    issues = []
    street_counts = defaultdict(list)

    for store in stores:
        lat = store.get('lat', 0)
        lng = store.get('lng', 0)
        current_street = store.get('final_street', '未知')

        street_counts[current_street].append(store['id'])

        if current_street in STREET_BOUNDS:
            bounds = STREET_BOUNDS[current_street]["bounds"]
            if not is_in_bounds(lat, lng, bounds):
                center_lat = (bounds[0] + bounds[1]) / 2
                center_lng = (bounds[2] + bounds[3]) / 2
                dist_to_current = haversine_distance(lat, lng, center_lat, center_lng)
                best_street, best_dist = find_best_street(lat, lng)

                issues.append({
                    'id': store['id'],
                    'name': store['name'],
                    'addr': store.get('addr', ''),
                    'current': current_street,
                    'suggested': best_street,
                    'dist_to_current': dist_to_current
                })
        elif lat and lng:
            best_street, best_dist = find_best_street(lat, lng)
            issues.append({
                'id': store['id'],
                'name': store['name'],
                'addr': store.get('addr', ''),
                'current': current_street,
                'suggested': best_street,
                'dist_to_current': None
            })

    # 显示统计
    print("=" * 54)
    print("📍 街道分类检测报告")
    print("=" * 54)
    print()
    print("📊 当前门店分布：")
    for street, ids in sorted(street_counts.items(), key=lambda x: -len(x[1])):
        print(f"   {street}: {len(ids)} 家")

    if not issues:
        print()
        print("✅ 所有门店分类正常！")
        print()
        return

    print()
    print(f"⚠️  发现 {len(issues)} 个分类问题，已自动修正：")
    print("-" * 54)

    fixed_count = 0
    for issue in issues:
        old_street = issue['current']
        new_street = issue['suggested']

        # 修正 stores.json
        for store in stores:
            if store['id'] == issue['id']:
                store['final_street'] = new_street
                store['region'] = new_street
                break

        # 输出修正信息
        emoji = "🔴" if old_street != new_street else "🟡"
        print(f"  {emoji} #{issue['id']} {issue['name'][:18]}")
        print(f"     {old_street} → {new_street}")

        fixed_count += 1

    # 保存修正后的数据
    with open(STORES_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print()
    print(f"✅ 已自动修正 {fixed_count} 家门店，stores.json 已更新")
    print()
    print("💡 如需查看详情，运行: python check_streets.py")
    print()


# ============================================================
# 生成地图 HTML（复用离线模板，数据嵌入 JS）
# ============================================================
def generate_map_html(stores_json_str):
    """用离线模板生成地图，将门店数据嵌入 JS"""
    import json as _json
    stores = _json.loads(stores_json_str)

    # 读取离线模板
    offline_template = os.path.join(SCRIPT_DIR, "shop_map_offline.html")
    if not os.path.exists(offline_template):
        log(f"⚠️ 找不到模板文件 shop_map_offline.html，跳过 HTML 更新")
        return

    with open(offline_template, "r", encoding="utf-8") as f:
        html_content = f.read()

    # 构建 stores JS 数组字符串（使用 final_street 作为区域）
    store_lines = []
    for s in stores:
        lat = s.get("lat") or 0
        lng = s.get("lng") or 0
        name = s["name"].replace('"', '\\"')
        addr = s["addr"].replace('"', '\\"')
        # 优先使用 final_street（标准化街道），其次使用原始 region
        region = s.get("final_street") or s.get("region", "其他")
        region = region.replace('"', '\\"')
        status = s.get("status", "未知").replace('"', '\\"')
        district = s.get("district", "")
        final_street = s.get("final_street", "")
        store_lines.append(
            f'{{id:{s["id"]},name:"{name}",addr:"{addr}",region:"{region}",status:"{status}",lat:{lat},lng:{lng},district:"{district}",final_street:"{final_street}"}}'
        )
    stores_js = "[\n        " + ",\n        ".join(store_lines) + "\n    ]"

    # 替换模板中的 stores 数据块
    import re
    pattern = r'const stores = \[.*?\];'
    if re.search(pattern, html_content, re.DOTALL):
        html_content = re.sub(pattern, f'const stores = {stores_js};', html_content, flags=re.DOTALL)
    else:
        log(f"⚠️ 未找到 stores 数据块，尝试字符串替换")
        old = 'const stores = ['
        if old in html_content:
            end = html_content.index('];\n', html_content.index(old)) + 2
            html_content = html_content[:html_content.index(old)] + f'const stores = {stores_js};' + html_content[end:]

    with open(CURRENT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)


if __name__ == "__main__":
    main()
