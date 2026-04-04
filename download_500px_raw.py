#!/usr/bin/env python3
"""500px 鲩鱼图片下载器 - 使用并发curl下载!raw原图"""
import os
import re
import subprocess
import concurrent.futures

# 图片数据（从浏览器收集）
images = [
    {"index": 1, "url": "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/d77447900f154f1c941896fa019d2057.jpg!raw", "alt": "蒸鱼淋油"},
    {"index": 2, "url": "https://img.500px.me/photo/b398ec104477bae3df5280144282b6595/5b54e72b3d2243328454c1a226b2cb44.jpg!raw", "alt": "家常红烧青鱼块12"},
    {"index": 3, "url": "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/7fdc570bf90e4778a6ae54526edfc6c0.jpg!raw", "alt": "顺德大条鲩鱼鱼生刺身"},
    {"index": 4, "url": "https://img.500px.me/photo/50facfd154829804d3b3a136d21008353/5766ebf2dea34d8592d8b2356c8a572f.jpg!raw", "alt": "怀旧八十年代老重庆居民区楼下的市井火锅脆鱼片"},
    {"index": 5, "url": "https://img.500px.me/photo/f8aa339d2496cb81333b6286ef0a91454/b0f622822b644f53a695ffe2f86154e4.jpg!raw", "alt": "鲜鱼肉片"},
    {"index": 6, "url": "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/e899122c902a4d019d24ff4974c9da09.jpg!raw", "alt": "顺德大条鲩鱼鱼生刺身"},
    {"index": 7, "url": "https://img.500px.me/photo/b398ec104477bae3df5280144282b6595/c53c55405f8240b9adf8d26ad5905d23.jpg!raw", "alt": "铁锅煎腌鱼块7"},
    {"index": 8, "url": "https://img.500px.me/photo/f8aa339d2496cb81333b6286ef0a91454/035eefe1d4074d708f9615be7112104d.jpg!raw", "alt": "簸箕水库鱼"},
    {"index": 9, "url": "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/03a2b9d30c0540719ea08fbb8966e2f6.jpg!raw", "alt": "湘菜石锅蒸鱼"},
    {"index": 10, "url": "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/3fab5491f95649a9908e52d6c01d1d71.jpg!raw", "alt": "顺德大条鲩鱼鱼生刺身"},
    {"index": 11, "url": "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/66975bd138aa4eecb45e9a9f9f34ae23.jpg!raw", "alt": "湘菜石锅蒸鱼"},
    {"index": 12, "url": "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/51898e2bb8824c09836af3f654e7380a.jpg!raw", "alt": "啫啫草鱼块"},
    {"index": 13, "url": "https://img.500px.me/photo/50facfd154829804d3b3a136d21008353/424f44e425ae4355a6b9693b6b37cc14.jpg!raw", "alt": "怀旧八十年代老重庆居民区楼下的市井火锅脆鱼片"},
    {"index": 14, "url": "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/34558f5660664fcc8a3521c9e8df0720.jpg!raw", "alt": "啫啫草鱼块"},
    {"index": 15, "url": "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/c50da35adeee437e825ccedf484e2710.jpg!raw", "alt": "湘菜石锅蒸鱼"},
    {"index": 16, "url": "https://img.500px.me/photo/b44d8ec784a9c9870a208559574722711/75cf27bd0c9246ebbc9f2b4f8fb09713.jpg!raw", "alt": "油盐清蒸鲩鱼"},
    {"index": 17, "url": "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/d292aa23cc2e413b98e7b2d48b8501ab.jpg!raw", "alt": "啫啫鱼头煲"},
    {"index": 18, "url": "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/07e0bf70cd1c46e99911a9ba37491213.jpg!raw", "alt": "啫啫金汤鱼煲"},
    {"index": 19, "url": "https://img.500px.me/photo/39c7818a24011a2221827da5977ee6328/a7cad21127a4430da61145520d6e6007.jpg!raw", "alt": "营养膳食清蒸功夫鲩鱼"},
    {"index": 20, "url": "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/a3593ad31ea54ab88b1a8d9a1fb6d4d0.jpg!raw", "alt": "湘菜石锅蒸鱼"},
    {"index": 21, "url": "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/5f5b3e72def24a4e8e68fb75ccc1351a.jpg!raw", "alt": "顺德大条鲩鱼鱼生刺身"},
    {"index": 22, "url": "https://img.500px.me/photo/f8aa339d2496cb81333b6286ef0a91454/9ab81c500f5741a39d2726ad0646a27b.jpg!raw", "alt": "鱼肉粉"},
    {"index": 23, "url": "https://img.500px.me/photo/2daae947f4d24a584f52ef366a6287939/971d192c0c9c4f97b93f6cb3982ab3ae.jpg!raw", "alt": "清蒸无骨鲩鱼"},
    {"index": 24, "url": "https://img.500px.me/photo/bac3e1deb4eb8bb5d940de84a57842906/0adcdfae400e4881955403888573ca97.jpg!raw", "alt": "广东中山特色美食脆肉鲩火锅"},
    {"index": 25, "url": "https://img.500px.me/photo/31121dd8248f4873bb43361496fb04802/49ac1ea5748947468a120586e94eaaf6.jpg!raw", "alt": "清蒸鲩鱼"},
    {"index": 26, "url": "https://img.500px.me/photo/ca80529b7400b87e83ee40806fe969464/0f9ab1190c59423a95a6c10badda1338.jpg!raw", "alt": "石斑鱼蒸石斑鱼等"},
    {"index": 27, "url": "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/530f598c0b1c495fa788b1addf45b100.jpg!raw", "alt": "蒸鱼淋油"},
    {"index": 28, "url": "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/c7c259fcd12144e1ac933e1c8224862d.jpg!raw", "alt": "啫啫脆肉鲩"},
    {"index": 29, "url": "https://img.500px.me/photo/402cc07c746658d0b20035a5f4c858874/385e7ea7084a4dbe9c7776be264bece6.jpg!raw", "alt": "盘子中的脆肉鲩脆鱼特写"},
    {"index": 30, "url": "https://img.500px.me/photo/dbbbb8c384fa19618cd9ddb2c86992586/0d567d71c7d349ffbcb2ae7befd7b778.jpeg!raw", "alt": "顺德鱼生"},
    {"index": 31, "url": "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/631e312be6124d428be24bcef29ac40e.jpg!raw", "alt": "啫啫脆肉鲩"},
    {"index": 32, "url": "https://img.500px.me/photo/ca80529b7400b87e83ee40806fe969464/44c5a9710fd2421fb6255511ba701d22.jpg!raw", "alt": "石斑鱼蒸石斑鱼等2"},
    {"index": 33, "url": "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/7d7b00a9ae0a4ec6be0f912c78c5e663.jpg!raw", "alt": "啫啫脆肉鲩"},
    {"index": 34, "url": "https://img.500px.me/photo/f8aa339d2496cb81333b6286ef0a91454/3186ffc5f8a243478ae68b271b2b39ae.jpg!raw", "alt": "脆肉鲩砂锅粥"},
    {"index": 35, "url": "https://img.500px.me/photo/ef697bd5742bd9848dd9bdf2482e26993/41acced638014da4a7cbee44fea9ad1a.jpg!raw", "alt": "生鲩鱼片特写生鱼片"},
    {"index": 36, "url": "https://img.500px.me/photo/7022db791467b9b6aa3f18176686b8451/1e4f5fcf02954a65bbdc33d170f0f229.jpg!raw", "alt": "餐桌上盘子里的食物的高角度视图"},
    {"index": 37, "url": "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/e8381c8dec84442186b6bee9cf9ae19c.jpg!raw", "alt": "啫啫脆肉鲩"},
    {"index": 38, "url": "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/d824ea74a8fc43b19a50222595c86cbe.jpg!raw", "alt": "啫啫脆肉鲩"},
    {"index": 39, "url": "https://img.500px.me/photo/f8aa339d2496cb81333b6286ef0a91454/e147ecdf7f9347e1a85ff9ef179abc0a.jpg!raw", "alt": "脆肉鲩河粉"},
    {"index": 40, "url": "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/ade6b0da097646bfa2c9ab715358ae2c.jpg!raw", "alt": "啫啫脆肉鲩"},
    {"index": 41, "url": "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/9189c09f127144f997ef8287337bcd43.jpg!raw", "alt": "啫啫金汤鱼煲"},
    {"index": 42, "url": "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/ca8820497f3a4e17bfbe9eb491ddaad3.jpg!raw", "alt": "啫啫脆肉鲩"},
    {"index": 43, "url": "https://img.500px.me/photo/b398ec104477bae3df5280144282b6595/a3d8d4fc01fd40e1baea54efe08d1695.jpg!raw", "alt": "风干的地方特色美食腌腊鱼4"},
    {"index": 44, "url": "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/05d6e4024e3b48d0a836836fbe00c1a7.jpg!raw", "alt": "湘菜石锅蒸鱼"},
    {"index": 45, "url": "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/ab675f0ed00349ac868076ba9cc56e56.jpg!raw", "alt": "湘菜石锅蒸鱼"},
    {"index": 46, "url": "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/7c95b243c1574bf1be0f706b962c1932.jpg!raw", "alt": "啫啫金汤鱼煲"},
    {"index": 47, "url": "https://img.500px.me/gicPicture/9d27b13c7452d9b548b5b5fb8ae682612/fa0a864c816e44648b15af5841e03a66.jpg!raw", "alt": "湘菜石锅蒸鱼"},
    {"index": 48, "url": "https://img.500px.me/photo/f8aa339d2496cb81333b6286ef0a91454/4cef58d352944d1fbd3f3eb6468bc3e2.jpg!raw", "alt": "鲜鱼肉片"},
    {"index": 49, "url": "https://img.500px.me/photo/31121dd8248f4873bb43361496fb04802/a641e26a53c443f2a4df5876f936f2ed.jpg!raw", "alt": "清蒸鲩鱼"},
    {"index": 50, "url": "https://img.500px.me/photo/dbbbb8c384fa19618cd9ddb2c86992586/17b41d95f8b0421fa97f291ab95e3c98.jpeg!raw", "alt": "顺德鱼生"},
    {"index": 51, "url": "https://img.500px.me/photo/ca80529b7400b87e83ee40806fe969464/1cecae4197194d94acea00f0d7ed1543.jpg!raw", "alt": "番茄火锅鱼酸汤鱼等"},
    {"index": 52, "url": "https://img.500px.me/photo/ef697bd5742bd9848dd9bdf2482e26993/04819d0e262644bea1b51c8e8c328a06.jpg!raw", "alt": "脆肉鲩生鱼片特写"},
    {"index": 53, "url": "https://img.500px.me/photo/39c7818a24011a2221827da5977ee6328/465ca23c5b7e4e3e97c51def071cd88e.jpg!raw", "alt": "粤菜清蒸鲩鱼油盐蒸鲩鱼清蒸鱼"},
    {"index": 54, "url": "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/2ad44fe31ab148018ad0759b93368a31.jpg!raw", "alt": "啫啫鱼头煲"},
    {"index": 55, "url": "https://img.500px.me/gicPicture/f8aa339d2496cb81333b6286ef0a91454/2ee74ae852db40d8bbea51b716892520.jpg!raw", "alt": "啫啫金汤鱼煲"},
]

OUTPUT_DIR = os.path.expanduser("~/Downloads/500px鲩鱼")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def sanitize_filename(name):
    """清理文件名，移除非法字符"""
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', '_', name)
    return name[:40]

def get_ext(url):
    if '.jpeg' in url.lower() or '.jpg' in url.lower():
        return '.jpg'
    elif '.png' in url.lower():
        return '.png'
    elif '.gif' in url.lower():
        return '.gif'
    elif '.webp' in url.lower():
        return '.webp'
    return '.jpg'

COOKIE = 'access_token=6B7E8DE33C6F30B827CC0BF04E1971E5DBB6ACF90C047FA18A608948F1A3CBE18D7C36E3FF1364E5C08BEB51FFC39C3DB2C73192FA68E62F82EC2F07ED4F77D3580DE629F6B559A0593E836917C91EA16F739752505643B48C1E5D516707317AFB2225796F1A73BCAC58C3FCC5209475A6AEBAAD137727B3; token=Token-44d85690-061a-4f61-a62b-b8268a883f16; userId=0874d166e497aa04364cbf6ad56be2732; sajssdk_2015_cross_new_user=1; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%220874d166e497aa04364cbf6ad56be2732%22%2C%22first_id%22%3A%2219d57faf753129a-0c50c739bd203b8-19525631-921600-19d57faf7542104%22%2C%22props%22%3A%7B%7D%2C%22%24device_id%22%3A%2219d57faf753129a-0c50c739bd203b8-19525631-921600-19d57faf7542104%22%7D; Hm_lvt_3eea10d35cb3423b367886fc968de15a=1775297538; Hm_lpvt_3eea10d35cb3423b367886fc968de15a=1775297561'

def download_one(img):
    idx, url, alt = img['index'], img['url'], img['alt']
    safe_alt = sanitize_filename(alt)
    ext = get_ext(url)
    filename = f"{idx:03d}_{safe_alt}{ext}"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    # 如果文件已存在，跳过
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        return {'index': idx, 'status': 'skipped', 'filename': filename, 'size': size}
    
    # 下载 - 使用登录cookies
    cmd = [
        'curl', '-s', '-L', '-o', filepath,
        '-A', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        '-H', f'Cookie: {COOKIE}',
        '-H', 'Referer: https://500px.com.cn/',
        '-H', 'Origin: https://500px.com.cn',
        '--max-time', '30',
        url
    ]
    
    try:
        result = subprocess.run(cmd, timeout=35, capture_output=True)
        if result.returncode == 0 and os.path.exists(filepath):
            size = os.path.getsize(filepath)
            if size > 5000:
                return {'index': idx, 'status': 'success', 'filename': filename, 'size': size}
            else:
                if os.path.exists(filepath):
                    os.remove(filepath)
                return {'index': idx, 'status': 'failed', 'reason': 'file_too_small', 'filename': filename}
        else:
            if os.path.exists(filepath):
                os.remove(filepath)
            return {'index': idx, 'status': 'failed', 'reason': 'curl_error', 'filename': filename}
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return {'index': idx, 'status': 'failed', 'reason': str(e), 'filename': filename}

def main():
    total = len(images)
    print(f"📥 开始下载 {total} 张 500px 原图（!raw 高清版）...")
    print(f"📁 保存目录: {OUTPUT_DIR}\n")
    
    success = 0
    failed = 0
    skipped = 0
    
    # 并发下载（8个并发）
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(download_one, img): img for img in images}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            idx = result['index']
            
            if result['status'] == 'success':
                size_kb = result['size'] // 1024
                print(f"  ✅ [{idx:02d}/{total}] {result['filename']} ({size_kb}KB)")
                success += 1
            elif result['status'] == 'skipped':
                print(f"  ⏭️  [{idx:02d}/{total}] 已存在，跳过: {result['filename']}")
                skipped += 1
            else:
                print(f"  ❌ [{idx:02d}/{total}] 失败: {result['filename']} ({result.get('reason', 'unknown')})")
                failed += 1
    
    print(f"\n{'='*50}")
    print(f"🎉 下载完成！")
    print(f"   ✅ 成功: {success}/{total}")
    print(f"   ⏭️  跳过: {skipped}")
    print(f"   ❌ 失败: {failed}")
    print(f"   📁 保存目录: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
