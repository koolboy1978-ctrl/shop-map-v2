#!/usr/bin/env python3
"""
500px 鲩鱼图片批量下载脚本
自动滚动页面、点击加载更多、收集图片URL、下载原图到本地
"""

import asyncio
import os
import re
import time
from playwright.async_api import async_playwright

OUTPUT_DIR = os.path.expanduser("~/Downloads/500px鲩鱼")
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=[
            '--disable-blink-features=AutomationControlled',
            '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        ])
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        
        print("🚀 正在打开500px搜索页面...")
        await page.goto(
            "https://500px.com.cn/community/search?key=%E9%B2%A9%E9%B1%BC&searchtype=photos",
            wait_until="networkidle",
            timeout=30000
        )
        
        # 等待页面加载
        await asyncio.sleep(3)
        
        all_image_urls = []
        all_titles = []
        
        # 滚动加载 + 点击更多按钮
        max_cycles = 25
        for cycle in range(max_cycles):
            # 滚动到页面底部
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1.5)
            
            # 检查加载更多按钮
            more_btn = await page.query_selector('.more')
            if more_btn:
                # 滚动按钮到视口
                await more_btn.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)
                try:
                    await more_btn.click(timeout=3000)
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"   点击更多按钮失败: {e}")
            else:
                print("   未找到更多按钮")
            
            current_height = await page.evaluate("document.body.scrollHeight")
            print(f"   第 {cycle+1} 轮: scrollHeight={current_height}, 已收集URL数={len(all_image_urls)}")
            
            # 检查是否已加载足够内容
            if cycle > 5:
                # 连续两轮页面高度不变且无更多按钮，认为已到尽头
                pass
        
        # 最终滚动确保所有懒加载完成
        print("\n📜 执行最终滚动，确保所有图片加载...")
        for _ in range(5):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
        
        # 收集所有图片URL
        print("\n📷 收集图片URL...")
        img_data = await page.evaluate("""
            () => {
                const imgs = document.querySelectorAll('img.copyright-contextmenu');
                const results = [];
                imgs.forEach((img, i) => {
                    const src = img.src || img.dataset.src;
                    if (src && !src.includes('data:image/gif') && src.includes('500px')) {
                        results.push({
                            src: src,
                            alt: img.alt || 'untitled'
                        });
                    }
                });
                return results;
            }
        """)
        
        print(f"   共收集到 {len(img_data)} 个图片URL")
        
        # 显示样本
        for i, item in enumerate(img_data[:3]):
            print(f"   [{i+1}] {item['alt']}: {item['src'][:80]}...")
        
        await browser.close()
        
        # ========== 处理URL并下载 ==========
        print(f"\n📥 开始下载 {len(img_data)} 张图片到 {OUTPUT_DIR}")
        
        import subprocess
        
        success = 0
        failed = 0
        skipped = 0
        
        for i, item in enumerate(img_data):
            src = item['src']
            alt = item['alt'].replace('摄影照片', '').strip() or f'鲩鱼_{i+1}'
            
            # 清理文件名
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', alt)[:50]
            
            # 尝试获取原图URL（去掉 !p4 等后缀）
            # 500px URL格式: https://img.500px.me/photo/xxx.jpg!p4
            # 尝试去掉 !p4 或替换为更高质量
            original_url = src
            if '!p' in src:
                # 尝试去掉质量后缀获取原图
                original_url = src.split('!')[0]
            
            # 确定文件扩展名
            if '.jpg' in original_url.lower() or '.jpeg' in original_url.lower():
                ext = '.jpg'
            elif '.png' in original_url.lower():
                ext = '.png'
            else:
                ext = '.jpg'
            
            filename = f"{i+1:03d}_{safe_name}{ext}"
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            # 如果文件已存在，跳过
            if os.path.exists(filepath):
                print(f"   ⏭️  [{i+1}/{len(img_data)}] 已存在，跳过: {filename}")
                skipped += 1
                continue
            
            # 下载图片
            cmd = ['curl', '-s', '-L', '-o', filepath, '-A', 
                   'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                   original_url]
            
            try:
                result = subprocess.run(cmd, timeout=30, capture_output=True)
                if result.returncode == 0 and os.path.exists(filepath):
                    size = os.path.getsize(filepath)
                    if size > 5000:  # 文件大于5KB认为下载成功
                        print(f"   ✅ [{i+1}/{len(img_data)}] {filename} ({size//1024}KB)")
                        success += 1
                    else:
                        os.remove(filepath)
                        print(f"   ❌ [{i+1}/{len(img_data)}] 文件过小/下载失败: {filename}")
                        failed += 1
                else:
                    print(f"   ❌ [{i+1}/{len(img_data)}] curl失败: {filename}")
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    failed += 1
            except Exception as e:
                print(f"   ❌ [{i+1}/{len(img_data)}] 异常: {e} - {filename}")
                if os.path.exists(filepath):
                    os.remove(filepath)
                failed += 1
        
        print(f"\n🎉 下载完成！")
        print(f"   ✅ 成功: {success}")
        print(f"   ⏭️  跳过: {skipped}")
        print(f"   ❌ 失败: {failed}")
        print(f"   📁 保存目录: {OUTPUT_DIR}")

if __name__ == "__main__":
    asyncio.run(main())
