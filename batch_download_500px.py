#!/usr/bin/env python3
"""
500px 批量图片下载脚本
依次搜索多个关键词，滚动加载全部图片，Playwright截图保存
"""
import asyncio
import os
import json
import time
from playwright.async_api import async_playwright

# ===================== 可配置参数 =====================
OUTPUT_BASE = os.path.expanduser("~/Downloads/500px鱼类图集")
HEADLESS = True
SCREENSHOT_QUALITY = 95  # JPEG质量

KEYWORDS = [
    "草鱼",
    "皖鱼",
    "草鲩",
    "大头鱼",
    "鳙鱼",
    "花鲢",
    "胖头鱼",
    "包头鱼",
    "黑鲢",
    "青竹鱼",
    "青竹鲤",
    "竹鲃鲤",
    "青鲋鲤",
    "赤眼鱼",
    "赤眼鳟",
    "军鱼",
    "光倒刺鲃",
    "粗鳞鱼",
    "坑塘鱼",
]

COOKIES = [
    {"name": "access_token", "value": "6B7E8DE33C6F30B827CC0BF04E1971E5DBB6ACF90C047FA18A608948F1A3CBE18D7C36E3FF1364E5C08BEB51FFC39C3DB2C73192FA68E62F82EC2F07ED4F77D3580DE629F6B559A0593E836917C91EA16F739752505643B48C1E5D516707317AFB2225796F1A73BCAC58C3FCC5209475A6AEBAAD137727B3", "url": "https://500px.com.cn/"},
    {"name": "token", "value": "Token-44d85690-061a-4f61-a62b-b8268a883f16", "url": "https://500px.com.cn/"},
    {"name": "userId", "value": "0874d166e497aa04364cbf6ad56be2732", "url": "https://500px.com.cn/"},
]


def sanitize(name):
    """清理文件名，去除不合法字符"""
    import re
    name = re.sub(r'[/\\:*?"<>|]', '', name)
    name = name.strip()
    if not name:
        return "未命名"
    return name[:40]  # 限制长度


async def wait_page_loaded(page):
    """等待页面加载"""
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=10000)
    except:
        pass
    await asyncio.sleep(2)


async def close_popups(page):
    """关闭弹窗遮罩"""
    await page.evaluate("""() => {
        const mask = document.getElementById('dialog-box-mask');
        if (mask) mask.remove();
        document.querySelectorAll('[class*="mask"], [class*="dialog"], [class*="popup"], [class*="modal"]').forEach(el => {
            if (el.id !== 'dialog-box-mask' && window.getComputedStyle(el).position === 'fixed') {
                el.remove();
            }
        });
    }""")


async def scroll_and_load_more(page, max_clicks=30):
    """滚动页面 + 点击更多按钮，加载全部内容"""
    print("  ↳ 滚动页面并点击「加载更多」...")
    prev_height = 0
    click_count = 0

    for i in range(max_clicks):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1.5)

        # 尝试点击更多按钮
        more_btn = await page.query_selector('.more')
        if more_btn:
            try:
                btn_visible = await more_btn.is_visible()
                if btn_visible:
                    await more_btn.scroll_into_view_if_needed()
                    await asyncio.sleep(0.5)
                    await more_btn.click()
                    click_count += 1
                    print(f"    点击第 {click_count} 次加载...")
                    await asyncio.sleep(2)

                    # 如果页面高度没变化，且按钮还在，可能到底了
                    current_height = await page.evaluate("document.body.scrollHeight")
                    if current_height == prev_height:
                        # 再检查一下
                        more_btn2 = await page.query_selector('.more')
                        if not more_btn2:
                            print("  ↳ 更多按钮已消失，到达底部")
                            break
                    prev_height = current_height
            except Exception as e:
                # 按钮可能消失或不可点击
                pass
        else:
            print("  ↳ 更多按钮已消失，到达底部")
            break

    print(f"  ↳ 共点击加载 {click_count} 次")


async def collect_image_urls(page):
    """收集页面上所有已加载的图片URL"""
    await asyncio.sleep(2)  # 等待懒加载完成

    data = await page.evaluate("""() => {
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
        const moreBtn = document.querySelector('.more');
        return {
            total: results.length,
            images: results,
            hasMoreBtn: !!moreBtn,
            scrollHeight: document.body.scrollHeight
        };
    }""")
    return data


async def download_images_by_screenshot(page, images, output_dir, keyword):
    """使用Playwright截图方式下载图片"""
    os.makedirs(output_dir, exist_ok=True)
    downloaded = 0
    errors = 0

    for i, img_info in enumerate(images):
        url = img_info['src']
        alt = img_info.get('alt', 'untitled')
        safe_alt = sanitize(alt)
        filename = f"{i+1:03d}_{safe_alt}.jpg"
        filepath = os.path.join(output_dir, filename)

        if os.path.exists(filepath):
            print(f"    [{i+1}/{len(images)}] 跳过（已存在）: {filename}")
            downloaded += 1
            continue

        try:
            # 打开图片页面
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(2)

            # 关闭弹窗
            await close_popups(page)

            # 截图保存
            await page.screenshot(
                path=filepath,
                type="jpeg",
                quality=SCREENSHOT_QUALITY,
                full_page=False
            )

            file_size = os.path.getsize(filepath)
            print(f"    [{i+1}/{len(images)}] ✓ {filename} ({file_size//1024}KB)")
            downloaded += 1

        except Exception as e:
            errors += 1
            print(f"    [{i+1}/{len(images)}] ✗ 失败: {alt} - {str(e)[:50]}")

    return downloaded, errors


async def process_keyword(browser, keyword):
    """处理单个关键词：导航→加载→下载"""
    print(f"\n{'='*50}")
    print(f"处理关键词: {keyword}")
    print(f"{'='*50}")

    output_dir = os.path.join(OUTPUT_BASE, keyword)
    os.makedirs(output_dir, exist_ok=True)

    # 创建新页面
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        locale="zh-CN"
    )
    # 添加登录cookies
    await context.add_cookies(COOKIES)
    page = await context.new_page()

    try:
        # 导航到搜索页
        encoded_key = keyword.encode('utf-8')
        url = f"https://500px.com.cn/community/search?key={encoded_key.decode('latin1')}&searchtype=photos"
        # 正确构建URL
        import urllib.parse
        url = f"https://500px.com.cn/community/search?key={urllib.parse.quote(keyword)}&searchtype=photos"

        print(f"  ↳ 导航到: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(3)

        # 关闭弹窗
        await close_popups(page)

        # 滚动加载
        await scroll_and_load_more(page)

        # 收集图片
        data = await collect_image_urls(page)
        print(f"  ↳ 收集到 {data['total']} 张图片")

        if data['total'] == 0:
            print(f"  ⚠ 无图片，保存搜索页截图备用")
            await page.screenshot(path=os.path.join(output_dir, "search_page.jpg"), type="jpeg", quality=80)
            return 0, keyword

        # 下载图片
        downloaded, errors = await download_images_by_screenshot(
            page, data['images'], output_dir, keyword
        )
        print(f"\n  ✅ {keyword} 完成: {downloaded} 张成功, {errors} 张失败")

        # 保存URL清单
        urls_file = os.path.join(output_dir, "urls.json")
        with open(urls_file, 'w', encoding='utf-8') as f:
            json.dump(data['images'], f, ensure_ascii=False, indent=2)

        return downloaded, keyword

    except Exception as e:
        print(f"  ❌ {keyword} 出错: {e}")
        return 0, keyword
    finally:
        await page.close()
        await context.close()


async def main():
    print("=" * 60)
    print("500px 批量图片下载")
    print(f"关键词数量: {len(KEYWORDS)}")
    print(f"保存位置: {OUTPUT_BASE}")
    print("=" * 60)

    os.makedirs(OUTPUT_BASE, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)

        total_downloaded = 0
        results = []

        for i, keyword in enumerate(KEYWORDS):
            print(f"\n[{i+1}/{len(KEYWORDS)}]", end="")
            downloaded, kw = await process_keyword(browser, keyword)
            total_downloaded += downloaded
            results.append((kw, downloaded))

            # 每个关键词间隔2秒
            if i < len(KEYWORDS) - 1:
                await asyncio.sleep(2)

        await browser.close()

    # 打印汇总
    print("\n" + "=" * 60)
    print("下载汇总")
    print("=" * 60)
    for kw, count in results:
        print(f"  {kw}: {count} 张")
    print(f"\n总计: {total_downloaded} 张图片")
    print(f"保存位置: {OUTPUT_BASE}")


if __name__ == "__main__":
    asyncio.run(main())
