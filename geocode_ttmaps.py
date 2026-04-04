#!/usr/bin/env python3
"""
使用Playwright浏览器 + 腾讯地图网页版批量地理编码
无需API Key，通过网页搜索提取坐标
"""
import asyncio
import json
import time
import os
import sys
import pandas as pd
import urllib.parse
from playwright.async_api import async_playwright

EXCEL_FILE = "/Users/apple/WorkBuddy/图片提取/竞品店铺信息汇总.xlsx"
CACHE_FILE = "/Users/apple/WorkBuddy/图片提取/geocode_cache2.json"
OUTPUT_HTML = "/Users/apple/WorkBuddy/图片提取/竞品店铺地图.html"

# 读取数据
df = pd.read_excel(EXCEL_FILE, header=1)
df = df[df['序号'].notna() & (df['序号'] != '序号')].copy()
df['序号'] = df['序号'].astype(int)

# 加载缓存
cache = {}
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r') as f:
        cache = json.load(f)

async def geocode_one(page, address, seq, name):
    """在腾讯地图网页搜索地址，提取坐标"""
    cache_key = f"{seq}_{address[:20]}"
    if cache_key in cache:
        result = cache[cache_key]
        if result.get('lat'):
            return result

    try:
        search_url = f"https://map.qq.com/?word={urllib.parse.quote(address)}&center=latlng&_p=0,0&zoom=15"
        await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(3)

        # 从页面提取坐标
        result = await page.evaluate("""() => {
            // 方法1: 从URL参数
            if (window.__SEARCH_RESULT__) {
                return window.__SEARCH_RESULT__;
            }
            // 方法2: 从地图容器
            const mapEl = document.querySelector('#mapContainer, .map-container, [id*="map"]');
            if (mapEl && mapEl.dataset) {
                return mapEl.dataset;
            }
            // 方法3: 从页面文本搜索坐标
            const body = document.body.innerText;
            const coordMatch = body.match(/(\\d+\\.\\d{4,}),\\s*(\\d+\\.\\d{4,})/);
            if (coordMatch) {
                return { lat: parseFloat(coordMatch[1]), lng: parseFloat(coordMatch[2]) };
            }
            // 方法4: 查找搜索结果中的坐标
            const links = document.querySelectorAll('a[href*="latlng"], [data-lat], [data-lng]');
            for (const l of links) {
                const lat = l.dataset.lat || (l.href.match(/latlng=([^,&]+)/) || [])[1];
                const lng = l.dataset.lng || (l.href.match(/lng=([^,&]+)/) || [])[1];
                if (lat && lng) {
                    return { lat: parseFloat(lat), lng: parseFloat(lng) };
                }
            }
            // 方法5: 腾讯地图URL中的坐标
            const urlMatch = location.href.match(/center=latlng&_p=([^,&]+),([^,&]+)/);
            if (urlMatch) {
                return { lat: parseFloat(urlMatch[2]), lng: parseFloat(urlMatch[1]) };
            }
            return null;
        }""")

        if result and result.get('lat') and result.get('lng'):
            lat = result['lat']
            lng = result['lng']
            print(f"  ✓ {seq}. {name[:20]} → ({lat:.5f}, {lng:.5f})")
            cache[cache_key] = {'lat': lat, 'lng': lng, 'name': name}
            with open(CACHE_FILE, 'w') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            return {'lat': lat, 'lng': lng}

        # 方法6: 直接导航到坐标页面
        await page.goto(search_url, wait_until="networkidle", timeout=20000)
        await asyncio.sleep(4)

        # 尝试从地图iframe获取
        coord = await page.evaluate("""() => {
            // 查找腾讯地图的主地图iframe或容器
            const iframes = document.querySelectorAll('iframe');
            for (const iframe of iframes) {
                try {
                    const src = iframe.src || '';
                    const match = src.match(/latlng=([^,&]+),([^,&]+)/) ||
                                  src.match(/center=([^,&]+),([^,&]+)/);
                    if (match) {
                        return { lat: parseFloat(match[1]), lng: parseFloat(match[2]) };
                    }
                } catch(e) {}
            }
            // 从location
            const locMatch = location.href.match(/latlng=([^,&]+),([^,&]+)/);
            if (locMatch) {
                return { lat: parseFloat(locMatch[2]), lng: parseFloat(locMatch[1]) };
            }
            return null;
        }""")

        if coord and coord.get('lat'):
            lat = coord['lat']
            lng = coord['lng']
            print(f"  ✓ {seq}. {name[:20]} → ({lat:.5f}, {lng:.5f})")
            cache[cache_key] = {'lat': lat, 'lng': lng, 'name': name}
            with open(CACHE_FILE, 'w') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            return {'lat': lat, 'lng': lng}

        print(f"  ✗ {seq}. {name[:20]} → 无法提取坐标")

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
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        success_count = 0
        for i, row in df.iterrows():
            seq = int(row['序号'])
            name = str(row['店铺名称'])
            address = str(row['地址'])

            result = await geocode_one(page, address, seq, name)
            if result:
                success_count += 1

            # 每个地址间隔1秒
            await asyncio.sleep(1)

        await browser.close()

    print(f"\n地理编码完成：{success_count}/{len(df)} 成功")
    return success_count

if __name__ == "__main__":
    asyncio.run(main())
