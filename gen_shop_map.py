"""
竞品门店地图生成器
用法: python gen_shop_map.py [坐标文件.json]

在 shop_map_editor.html 中标注完所有37家门店后，
导出的 JSON 文件传入本脚本，即可生成完整的交互式地图。
"""

import json, sys, os

try:
    import folium
except ImportError:
    print("需要安装 folium: pip install folium")
    sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("用法: python gen_shop_map.py shop_coordinates.json")
        print("（坐标文件从 shop_map_editor.html 导出）")
        sys.exit(1)

    coords_file = sys.argv[1]
    if not os.path.exists(coords_file):
        print(f"文件不存在: {coords_file}")
        sys.exit(1)

    with open(coords_file, encoding='utf-8') as f:
        coords = json.load(f)

    print(f"读取到 {len(coords)} 个门店坐标")

    # 读取 Excel 补充详细信息
    try:
        import openpyxl
        wb = openpyxl.load_workbook('竞品店铺信息汇总.xlsx', data_only=True)
        ws = wb['竞品店铺信息汇总']
        stores = {}
        for row in ws.iter_rows(min_row=3, values_only=True):
            if row[0] and str(row[0]).strip():
                sid = int(row[0])
                stores[sid] = {
                    '序号': row[0],
                    '店铺名称': row[1],
                    '营业时间': row[2],
                    '地址': row[3],
                    '人均': row[4],
                    '口味': row[5],
                    '环境': row[6],
                    '服务': row[7],
                    '区域': row[9],
                    '营业状态': row[10],
                    '榜单': row[23],
                    '备注': row[25],
                }
    except Exception as e:
        print(f"读取Excel失败: {e}, 仅使用坐标数据")
        stores = {}

    REGION_COLORS = {
        '松岗': '#e74c3c',
        '沙井商圈': '#3498db',
        '公明商圈': '#9b59b6',
        '光明新区': '#f39c12',
        '田寮/长圳': '#1abc9c',
        '福永': '#e67e22',
        '宝安': '#2ecc71',
        '圳美': '#e91e63',
        '罗田/燕川': '#795548',
    }

    # 计算地图中心
    lats = [v['lat'] for v in coords.values() if v.get('lat')]
    lngs = [v['lng'] for v in coords.values() if v.get('lng')]
    if not lats:
        print("错误: 没有有效的坐标数据")
        sys.exit(1)

    center_lat = sum(lats) / len(lats)
    center_lng = sum(lngs) / len(lngs)
    print(f"地图中心: ({center_lat:.4f}, {center_lng:.4f})")

    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=13,
        tiles=None,
    )

    # 添加底图图层
    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
        attr='© OpenStreetMap contributors © CARTO',
        name='CartoDB 亮色',
        overlay=False,
    ).add_to(m)

    # 区域背景圆形
    from collections import defaultdict
    region_groups = defaultdict(list)
    for sid_str, data in coords.items():
        sid = int(sid_str)
        region = data.get('region', stores.get(sid, {}).get('区域', '未知'))
        region_groups[region].append((data['lat'], data['lng']))

    for region, positions in region_groups.items():
        if positions:
            avg_lat = sum(p[0] for p in positions) / len(positions)
            avg_lng = sum(p[1] for p in positions) / len(positions)
            color = REGION_COLORS.get(region, '#888888')
            folium.Circle(
                location=[avg_lat, avg_lng],
                radius=2000,
                color=color,
                fillColor=color,
                fillOpacity=0.12,
                weight=2,
                dashArray='6,6',
                popup=f"<b>{region}</b><br>{len(positions)}家门店",
            ).add_to(m)

    # 门店标注
    for sid_str, data in coords.items():
        sid = int(sid_str)
        lat, lng = data['lat'], data['lng']
        store = stores.get(sid, {})
        region = data.get('region') or store.get('区域', '未知')
        color = REGION_COLORS.get(region, '#888888')

        name = data.get('name') or store.get('店铺名称', f'门店{sid}')
        addr = data.get('addr') or store.get('地址', '')
        status = store.get('营业状态', '未知')
        taste = store.get('口味', '')
        env = store.get('环境', '')
        service = store.get('服务', '')
        rank = store.get('榜单', '')
        note = store.get('备注', '')

        status_icon = '🟢' if status == '营业中' else ('🟡' if status == '即将营业' else '🔴')
        status_color = '#27ae60' if status == '营业中' else ('#f39c12' if status == '即将营业' else '#e74c3c')

        popup_html = f"""
        <div style="font-family:'PingFang SC','Microsoft YaHei',sans-serif;width:260px">
          <div style="font-size:14px;font-weight:bold;color:#2c3e50;margin-bottom:6px;border-bottom:2px solid {color};padding-bottom:6px">
            <span style="color:{color}">[{sid}]</span> {name}
          </div>
          <table style="font-size:12px;width:100%;border-collapse:collapse">
            <tr><td style="padding:3px 0;color:#7f8c8d;width:55px">地址</td><td style="padding:3px 0;color:#2c3e50">{addr}</td></tr>
            <tr><td style="padding:3px 0;color:#7f8c8d">状态</td><td style="padding:3px 0;color:{status_color};font-weight:bold">{status_icon} {status}</td></tr>
            {'<tr><td style="padding:3px 0;color:#7f8c8d">评分</td><td style="padding:3px 0">🍖 口味 '+str(taste)+' &nbsp;🏠 环境 '+str(env)+' &nbsp;🙋 服务 '+str(service)+'</td></tr>' if taste else ''}
            {'<tr><td style="padding:3px 0;color:#7f8c8d">榜单</td><td style="padding:3px 0;color:#9b59b6">'+str(rank)+'</td></tr>' if rank else ''}
            {'<tr><td style="padding:3px 0;color:#7f8c8d">备注</td><td style="padding:3px 0;color:#e67e22">'+str(note)+'</td></tr>' if note else ''}
          </table>
          <div style="font-size:10px;color:#bdc3c7;margin-top:6px;text-align:right">📌 {lat:.5f}, {lng:.5f}</div>
        </div>
        """

        folium.Marker(
            location=[lat, lng],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"[{sid}] {name}",
            icon=folium.DivIcon(
                html=f'''<div style="
                  width:30px;height:30px;border-radius:50% 50% 50% 0;
                  background:{color};border:3px solid white;box-shadow:0 2px 5px rgba(0,0,0,0.3);
                  transform:rotate(-45deg);display:flex;align-items:center;justify-content:center;
                  margin-left:-3px;margin-top:-3px;
                "><span style="transform:rotate(45deg);color:white;font-size:11px;font-weight:bold">{sid}</span></div>''',
                icon_size=(30, 30),
                icon_anchor=(15, 30),
            ),
        ).add_to(m)

    # 图例
    legend_html = '''
    <div style="position:fixed;bottom:30px;right:20px;background:white;
                padding:12px 16px;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.15);
                font-size:12px;font-family:sans-serif;z-index:9999;line-height:1.9">
      <b style="font-size:13px">📍 区域图例</b><br>
    '''
    for region, color in REGION_COLORS.items():
        count = len(region_groups.get(region, []))
        if count > 0:
            legend_html += f'<span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:{color};margin-right:6px"></span>{region} ({count})<br>'
    legend_html += '</div>'

    m.get_root().html.add_child(folium.Element(legend_html))

    # 标题
    title_html = '''
    <div style="position:fixed;top:10px;left:50%;transform:translateX(-50%);
                background:#2c3e50;color:white;padding:10px 24px;border-radius:20px;
                font-size:14px;font-weight:bold;z-index:9999;box-shadow:0 2px 10px rgba(0,0,0,0.2);
                font-family:sans-serif;white-space:nowrap">
      🗺️ 食为先·竞品门店分布地图（已标注 ''' + str(len(coords)) + '''/37家）
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    output = 'shop_map_final.html'
    m.save(output)
    print(f"✅ 地图已生成: {output}")
    print(f"   共标注 {len(coords)} 家门店")

if __name__ == '__main__':
    main()
