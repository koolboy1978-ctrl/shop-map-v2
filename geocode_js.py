#!/usr/bin/env python3
"""
使用腾讯地图JavaScript API地理编码（浏览器内调用，无需独立Key校验）
"""
import asyncio
import json
import os
import pandas as pd
from playwright.async_api import async_playwright

EXCEL_FILE = "/Users/apple/WorkBuddy/图片提取/竞品店铺信息汇总.xlsx"
CACHE_FILE = "/Users/apple/WorkBuddy/图片提取/geocode_cache3.json"

# 读取数据
df = pd.read_excel(EXCEL_FILE, header=1)
df = df[df['序号'].notna() & (df['序号'] != '序号')].copy()
df['序号'] = df['序号'].astype(int)

# 加载缓存
cache = {}
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r') as f:
        cache = json.load(f)

def save_cache():
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Geocode</title>
<script charset="utf-8" src="https://map.qq.com/api/js?v=2.exp&key=OB4BZ-D4W3U-B7VVO-4PJWW-6TKDJ-W6F7A"></script>
<style>body{margin:0;padding:20px;font-family:Arial}#result{white-space:pre-wrap;font-size:13px}</style>
</head>
<body>
<div id="result">READY</div>
<script>
var gc = new qq.maps.Geocoder({
    complete: function(result) {
        var loc = result.detail.location;
        document.getElementById('result').textContent = JSON.stringify({
            status: 'ok',
            lat: loc.lat,
            lng: loc.lng,
            address: result.detail.address
        });
    },
    error: function() {
        document.getElementById('result').textContent = JSON.stringify({status: 'error'});
    }
});

function doGeocode(address) {
    gc.getLocation(address);
}

// 监听地址变化
var lastAddr = '';
setInterval(function() {
    var addr = window.currentAddress;
    if (addr && addr !== lastAddr) {
        lastAddr = addr;
        gc.getLocation(addr);
    }
}, 500);

// 等待API加载
var checkCount = 0;
var checker = setInterval(function() {
    if (typeof qq !== 'undefined' && typeof qq.maps !== 'undefined' && typeof qq.maps.Geocoder !== 'undefined') {
        clearInterval(checker);
        document.getElementById('result').textContent = 'API_READY';
    }
    checkCount++;
    if (checkCount > 50) {
        clearInterval(checker);
        document.getElementById('result').textContent = 'API_TIMEOUT';
    }
}, 200);
</script>
</body>
</html>"""

async def geocode_with_browser(page, address, seq, name):
    """用浏览器内JS API地理编码"""
    cache_key = f"{seq}_{address[:20]}"
    if cache_key in cache and cache[cache_key].get('lat'):
        return cache[cache_key]

    try:
        # 创建一个内嵌HTML，直接调用腾讯地图JS API
        page2 = page
        # 用 evaluate_on_new_document 来设置初始状态
        await page.set_content(HTML_TEMPLATE, wait_until='domcontentloaded')

        # 等待API就绪
        for _ in range(30):
            await asyncio.sleep(0.5)
            status = await page.evaluate('() => document.getElementById("result").textContent')
            if status == 'API_READY':
                break
            elif status.startswith('{'):
                break

        if status == 'API_TIMEOUT':
            return None

        # 触发地理编码
        await page.evaluate(f'window.currentAddress = "{address}";')
        await asyncio.sleep(3)

        result_text = await page.evaluate('() => document.getElementById("result").textContent')
        if result_text and result_text.startswith('{'):
            data = json.loads(result_text)
            if data.get('status') == 'ok':
                lat = data['lat']
                lng = data['lng']
                print(f"  ✓ {seq}. {name[:20]} → ({lat:.5f}, {lng:.5f})")
                cache[cache_key] = {'lat': lat, 'lng': lng, 'name': name}
                save_cache()
                return {'lat': lat, 'lng': lng}

        print(f"  ✗ {seq}. {name[:20]} → 未找到 ({result_text})")

    except Exception as e:
        print(f"  ✗ {seq}. {name[:20]} → 错误: {str(e)[:50]}")

    cache[cache_key] = {'lat': None, 'lng': None}
    return None

async def main():
    print(f"开始地理编码，共 {len(df)} 个地址...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )

        success_count = 0
        for _, row in df.iterrows():
            seq = int(row['序号'])
            name = str(row['店铺名称'])
            address = str(row['地址'])

            page = await context.new_page()

            # 先访问腾讯地图主页初始化
            await page.goto('https://map.qq.com/', wait_until='domcontentloaded', timeout=10000)
            await asyncio.sleep(2)

            result = await geocode_with_browser(page, address, seq, name)
            if result:
                success_count += 1

            await page.close()
            await asyncio.sleep(1.5)  # 避免频率限制

        await browser.close()

    print(f"\n完成：{success_count}/{len(df)} 成功")
    print(f"缓存保存到: {CACHE_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
