#!/usr/bin/env python3
"""
500px 鲩鱼图片下载器 - 使用Playwright浏览器截图方式保存高清原图
绕过CDN直接访问限制，使用已登录的浏览器会话
"""
import asyncio
import base64
import os
import re
import json

async def main():
    async with AsyncPlaywright() as p:
        # 使用与MCP相同chromium，启动有痕模式
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                '--disable-web-security',
                '--allow-running-insecure-content',
            ]
        )
        
        # 创建上下文（可设置cookies）
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            ignore_https_errors=True,
        )
        
        # 设置登录cookies（需要url或domain+path）
        cookies = [
            {"name": "access_token", "value": "6B7E8DE33C6F30B827CC0BF04E1971E5DBB6ACF90C047FA18A608948F1A3CBE18D7C36E3FF1364E5C08BEB51FFC39C3DB2C73192FA68E62F82EC2F07ED4F77D3580DE629F6B559A0593E836917C91EA16F739752505643B48C1E5D516707317AFB2225796F1A73BCAC58C3FCC5209475A6AEBAAD137727B3", "url": "https://500px.com.cn/"},
            {"name": "token", "value": "Token-44d85690-061a-4f61-a62b-b8268a883f16", "url": "https://500px.com.cn/"},
            {"name": "userId", "value": "0874d166e497aa04364cbf6ad56be2732", "url": "https://500px.com.cn/"},
        ]
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        # 先打开主站建立会话
        print("🔐 建立会话...")
        await page.goto("https://500px.com.cn/", wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(3)
        
        OUTPUT_DIR = os.path.expanduser("~/Downloads/500px鲩鱼")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # 图片URL列表
        images = [
            (1, "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/d77447900f154f1c941896fa019d2057.jpg!p4", "蒸鱼淋油"),
            (2, "https://img.500px.me/photo/b398ec104477bae3df5280144282b6595/5b54e72b3d2243328454c1a226b2cb44.jpg!p4", "家常红烧青鱼块12"),
            (3, "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/7fdc570bf90e4778a6ae54526edfc6c0.jpg!p4", "顺德大条鲩鱼鱼生刺身"),
            (4, "https://img.500px.me/photo/50facfd154829804d3b3a136d21008353/5766ebf2dea34d8592d8b2356c8a572f.jpg!p4", "怀旧八十年代老重庆居民区楼下的市井火锅脆鱼片"),
            (5, "https://img.500px.me/photo/f8aa339d2496cb81333b6286ef0a91454/b0f622822b644f53a695ffe2f86154e4.jpg!p4", "鲜鱼肉片"),
            (6, "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/e899122c902a4d019d24ff4974c9da09.jpg!p4", "顺德大条鲩鱼鱼生刺身"),
            (7, "https://img.500px.me/photo/b398ec104477bae3df5280144282b6595/c53c55405f8240b9adf8d26ad5905d23.jpg!p4", "铁锅煎腌鱼块7"),
            (8, "https://img.500px.me/photo/f8aa339d2496cb81333b6286ef0a91454/035eefe1d4074d708f9615be7112104d.jpg!p4", "簸箕水库鱼"),
            (9, "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/03a2b9d30c0540719ea08fbb8966e2f6.jpg!p4", "湘菜石锅蒸鱼"),
            (10, "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/3fab5491f95649a9908e52d6c01d1d71.jpg!p4", "顺德大条鲩鱼鱼生刺身"),
            (11, "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/66975bd138aa4eecb45e9a9f9f34ae23.jpg!p4", "湘菜石锅蒸鱼"),
            (12, "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/51898e2bb8824c09836af3f654e7380a.jpg!p4", "啫啫草鱼块"),
            (13, "https://img.500px.me/photo/50facfd154829804d3b3a136d21008353/424f44e425ae4355a6b9693b6b37cc14.jpg!p4", "怀旧八十年代老重庆居民区楼下的市井火锅脆鱼片"),
            (14, "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/34558f5660664fcc8a3521c9e8df0720.jpg!p4", "啫啫草鱼块"),
            (15, "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/c50da35adeee437e825ccedf484e2710.jpg!p4", "湘菜石锅蒸鱼"),
            (16, "https://img.500px.me/photo/b44d8ec784a9c9870a208559574722711/75cf27bd0c9246ebbc9f2b4f8fb09713.jpg!p4", "油盐清蒸鲩鱼"),
            (17, "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/d292aa23cc2e413b98e7b2d48b8501ab.jpg!p4", "啫啫鱼头煲"),
            (18, "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/07e0bf70cd1c46e99911a9ba37491213.jpg!p4", "啫啫金汤鱼煲"),
            (19, "https://img.500px.me/photo/39c7818a24011a2221827da5977ee6328/a7cad21127a4430da61145520d6e6007.jpg!p4", "营养膳食清蒸功夫鲩鱼"),
            (20, "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/a3593ad31ea54ab88b1a8d9a1fb6d4d0.jpg!p4", "湘菜石锅蒸鱼"),
            (21, "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/5f5b3e72def24a4e8e68fb75ccc1351a.jpg!p4", "顺德大条鲩鱼鱼生刺身"),
            (22, "https://img.500px.me/photo/f8aa339d2496cb81333b6286ef0a91454/9ab81c500f5741a39d2726ad0646a27b.jpg!p4", "鱼肉粉"),
            (23, "https://img.500px.me/photo/2daae947f4d24a584f52ef366a6287939/971d192c0c9c4f97b93f6cb3982ab3ae.jpg!p4", "清蒸无骨鲩鱼"),
            (24, "https://img.500px.me/photo/bac3e1deb4eb8bb5d940de84a57842906/0adcdfae400e4881955403888573ca97.jpg!p4", "广东中山特色美食脆肉鲩火锅"),
            (25, "https://img.500px.me/photo/31121dd8248f4873bb43361496fb04802/49ac1ea5748947468a120586e94eaaf6.jpg!p4", "清蒸鲩鱼"),
            (26, "https://img.500px.me/photo/ca80529b7400b87e83ee40806fe969464/0f9ab1190c59423a95a6c10badda1338.jpg!p4", "石斑鱼蒸石斑鱼等"),
            (27, "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/530f598c0b1c495fa788b1addf45b100.jpg!p4", "蒸鱼淋油"),
            (28, "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/c7c259fcd12144e1ac933e1c8224862d.jpg!p4", "啫啫脆肉鲩"),
            (29, "https://img.500px.me/photo/402cc07c746658d0b20035a5f4c858874/385e7ea7084a4dbe9c7776be264bece6.jpg!p4", "盘子中的脆肉鲩脆鱼特写"),
            (30, "https://img.500px.me/photo/dbbbb8c384fa19618cd9ddb2c86992586/0d567d71c7d349ffbcb2ae7befd7b778.jpeg!p4", "顺德鱼生"),
            (31, "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/631e312be6124d428be24bcef29ac40e.jpg!p4", "啫啫脆肉鲩"),
            (32, "https://img.500px.me/photo/ca80529b7400b87e83ee40806fe969464/44c5a9710fd2421fb6255511ba701d22.jpg!p4", "石斑鱼蒸石斑鱼等2"),
            (33, "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/7d7b00a9ae0a4ec6be0f912c78c5e663.jpg!p4", "啫啫脆肉鲩"),
            (34, "https://img.500px.me/photo/f8aa339d2496cb81333b6286ef0a91454/3186ffc5f8a243478ae68b271b2b39ae.jpg!p4", "脆肉鲩砂锅粥"),
            (35, "https://img.500px.me/photo/ef697bd5742bd9848dd9bdf2482e26993/41acced638014da4a7cbee44fea9ad1a.jpg!p4", "生鲩鱼片特写生鱼片"),
            (36, "https://img.500px.me/photo/7022db791467b9b6aa3f18176686b8451/1e4f5fcf02954a65bbdc33d170f0f229.jpg!p4", "餐桌上盘子里的食物的高角度视图"),
            (37, "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/e8381c8dec84442186b6bee9cf9ae19c.jpg!p4", "啫啫脆肉鲩"),
            (38, "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/d824ea74a8fc43b19a50222595c86cbe.jpg!p4", "啫啫脆肉鲩"),
            (39, "https://img.500px.me/photo/f8aa339d2496cb81333b6286ef0a91454/e147ecdf7f9347e1a85ff9ef179abc0a.jpg!p4", "脆肉鲩河粉"),
            (40, "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/ade6b0da097646bfa2c9ab715358ae2c.jpg!p4", "啫啫脆肉鲩"),
            (41, "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/9189c09f127144f997ef8287337bcd43.jpg!p4", "啫啫金汤鱼煲"),
            (42, "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/ca8820497f3a4e17bfbe9eb491ddaad3.jpg!p4", "啫啫脆肉鲩"),
            (43, "https://img.500px.me/photo/b398ec104477bae3df5280144282b6595/a3d8d4fc01fd40e1baea54efe08d1695.jpg!p4", "风干的地方特色美食腌腊鱼4"),
            (44, "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/05d6e4024e3b48d0a836836fbe00c1a7.jpg!p4", "湘菜石锅蒸鱼"),
            (45, "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/ab675f0ed00349ac868076ba9cc56e56.jpg!p4", "湘菜石锅蒸鱼"),
            (46, "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/7c95b243c1574bf1be0f706b962c1932.jpg!p4", "啫啫金汤鱼煲"),
            (47, "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/fa0a864c816e44648b15af5841e03a66.jpg!p4", "湘菜石锅蒸鱼"),
            (48, "https://img.500px.me/photo/f8aa339d2496cb81333b6286ef0a91454/4cef58d352944d1fbd3f3eb6468bc3e2.jpg!p4", "鲜鱼肉片"),
            (49, "https://img.500px.me/photo/31121dd8248f4873bb43361496fb04802/a641e26a53c443f2a4df5876f936f2ed.jpg!p4", "清蒸鲩鱼"),
            (50, "https://img.500px.me/photo/dbbbb8c384fa19618cd9ddb2c86992586/17b41d95f8b0421fa97f291ab95e3c98.jpeg!p4", "顺德鱼生"),
            (51, "https://img.500px.me/photo/ca80529b7400b87e83ee40806fe969464/1cecae4197194d94acea00f0d7ed1543.jpg!p4", "番茄火锅鱼酸汤鱼等"),
            (52, "https://img.500px.me/photo/ef697bd5742bd9848dd9bdf2482e26993/04819d0e262644bea1b51c8e8c328a06.jpg!p4", "脆肉鲩生鱼片特写"),
            (53, "https://img.500px.me/photo/39c7818a24011a2221827da5977ee6328/465ca23c5b7e4e3e97c51def071cd88e.jpg!p4", "粤菜清蒸鲩鱼油盐蒸鲩鱼清蒸鱼"),
            (54, "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/2ad44fe31ab148018ad0759b93368a31.jpg!p4", "啫啫鱼头煲"),
            (55, "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/2ee74ae852db40d8bbea51b716892520.jpg!p4", "啫啫金汤鱼煲"),
        ]
        
        def sanitize(name):
            name = re.sub(r'[<>:"/\\|?*]', '_', name)
            name = re.sub(r'\s+', '_', name)
            return name[:40]
        
        total = len(images)
        success = 0
        failed = 0
        skipped = 0
        
        print(f"📥 开始下载 {total} 张图片（使用浏览器截图方式）...")
        print(f"📁 保存目录: {OUTPUT_DIR}\n")
        
        for idx, (num, url, alt) in enumerate(images):
            safe_alt = sanitize(alt)
            ext = '.jpg'
            filename = f"{num:03d}_{safe_alt}{ext}"
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            # 如果文件已存在，跳过
            if os.path.exists(filepath) and os.path.getsize(filepath) > 5000:
                print(f"  ⏭️  [{num:02d}/{total}] 已存在，跳过: {filename}")
                skipped += 1
                continue
            
            try:
                # 导航到图片URL
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(0.5)
                
                # 获取图片尺寸
                img_info = await page.evaluate("""() => {
                    const imgs = document.querySelectorAll('img');
                    if (imgs.length > 0) {
                        const img = imgs[0];
                        return { width: img.naturalWidth, height: img.naturalHeight, complete: img.complete };
                    }
                    return null;
                }""")
                
                if img_info and img_info['complete'] and img_info['width'] > 0:
                    w, h = img_info['width'], img_info['height']
                    # 设置viewport为图片尺寸
                    await page.set_viewport_size({"width": min(w + 20, 2000), "height": min(h + 20, 2000)})
                    await asyncio.sleep(0.3)
                    
                    # 截图保存
                    await page.screenshot(path=filepath, type='jpeg', quality=95)
                    size = os.path.getsize(filepath)
                    if size > 5000:
                        size_kb = size // 1024
                        print(f"  ✅ [{num:02d}/{total}] {filename} ({w}x{h}, {size_kb}KB)")
                        success += 1
                    else:
                        os.remove(filepath)
                        print(f"  ❌ [{num:02d}/{total}] 截图过小: {filename}")
                        failed += 1
                else:
                    print(f"  ❌ [{num:02d}/{total}] 图片加载失败: {filename}")
                    failed += 1
                    
            except Exception as e:
                print(f"  ❌ [{num:02d}/{total}] 异常: {str(e)[:50]} - {filename}")
                if os.path.exists(filepath):
                    os.remove(filepath)
                failed += 1
        
        await browser.close()
        
        print(f"\n{'='*50}")
        print(f"🎉 下载完成！")
        print(f"   ✅ 成功: {success}/{total}")
        print(f"   ⏭️  跳过: {skipped}")
        print(f"   ❌ 失败: {failed}")
        print(f"   📁 保存目录: {OUTPUT_DIR}")

if __name__ == "__main__":
    # 别名，兼容旧写法
    from playwright.async_api import async_playwright as AsyncPlaywright
    asyncio.run(main())
