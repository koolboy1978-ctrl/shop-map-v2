"""
竞品门店地图生成器 v2
- 读取 geocode_amap_results.json（高德 GCJ-02 坐标）
- 用 pygcj 库转换 GCJ-02 → WGS-84
- 生成 folium 交互式地图
"""

import json, os

try:
    import folium
except ImportError:
    print("需要安装 folium: pip install folium")
    exit(1)

try:
    from pygcj.pygcj import GCJProj
    _gcj_proj = GCJProj()
    def gcj02_to_wgs84(gcj_lng, gcj_lat):
        """GCJ-02 → WGS-84，传入 (lng, lat)，返回 (wgs_lng, wgs_lat)"""
        wgs_lat, wgs_lng = _gcj_proj.gcj_to_wgs(gcj_lat, gcj_lng)
        return wgs_lng, wgs_lat
except ImportError:
    print("需要安装 pygcj: pip install pygcj")
    exit(1)


# ========== 读取坐标数据 ==========
def load_coords():
    with open('geocode_amap_results.json', encoding='utf-8') as f:
        raw = json.load(f)

    coords = {}
    for sid, data in raw.items():
        sid = int(sid)
        if 'lat' in data and 'lng' in data:
            wgs_lng, wgs_lat = gcj02_to_wgs84(data['lng'], data['lat'])
            coords[sid] = {
                'wgs_lat': wgs_lat,
                'wgs_lng': wgs_lng,
                'gcj_lat': data['lat'],
                'gcj_lng': data['lng'],
                'name': data.get('name', ''),
                'addr': data.get('raw_addr', ''),
                'region': data.get('region', ''),
                'status': data.get('status', ''),
                'formatted': data.get('formatted', ''),
            }
    return coords


# ========== 读取 Excel 补充信息 ==========
def load_stores_detail():
    import openpyxl
    wb = openpyxl.load_workbook('竞品店铺信息汇总.xlsx', data_only=True)
    ws = wb['竞品店铺信息汇总']
    stores = {}
    for row in ws.iter_rows(min_row=3, values_only=True):
        if row[0] and str(row[0]).strip() and str(row[0]).isdigit():
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
    return stores


# ========== 生成地图 ==========
def generate_map():
    coords = load_coords()
    stores = load_stores_detail()

    print(f"共 {len(coords)} 家门店有坐标")

    # 计算中心
    lats = [v['wgs_lat'] for v in coords.values()]
    lngs = [v['wgs_lng'] for v in coords.values()]
    center_lat = sum(lats) / len(lats)
    center_lng = sum(lngs) / len(lngs)
    print(f"地图中心: ({center_lat:.4f}, {center_lng:.4f})")

    # 区域颜色
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

    # 创建地图
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=12,
        tiles=None,
    )

    # 底图：CartoDB 亮色（OSM系，WGS-84 正确显示）
    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
        attr='© OpenStreetMap contributors © CARTO',
        name='CartoDB 亮色底图',
        overlay=False,
    ).add_to(m)

    folium.TileLayer(
        tiles='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
        attr='© CARTO',
        name='CartoDB 暗色底图',
        overlay=False,
    ).add_to(m)

    # 区域统计
    from collections import defaultdict
    region_groups = defaultdict(list)
    for sid, data in coords.items():
        region_groups[data['region']].append((data['wgs_lat'], data['wgs_lng']))

    # 区域背景圆
    for region, positions in region_groups.items():
        if positions:
            avg_lat = sum(p[0] for p in positions) / len(positions)
            avg_lng = sum(p[1] for p in positions) / len(positions)
            color = REGION_COLORS.get(region, '#888888')
            folium.Circle(
                location=[avg_lat, avg_lng],
                radius=2200,
                color=color,
                fillColor=color,
                fillOpacity=0.10,
                weight=2,
                dashArray='6,6',
                popup=f"<b>{region}</b><br>{len(positions)} 家门店",
            ).add_to(m)

    # 门店标注
    for sid, data in coords.items():
        lat = data['wgs_lat']
        lng = data['wgs_lng']
        name = data['name']
        addr = data['addr']
        region = data['region']
        status = data['status']
        detail = stores.get(sid, {})

        color = REGION_COLORS.get(region, '#888888')
        status_icon = '🟢' if status == '营业中' else ('🟡' if status == '即将营业' else '🔴')
        status_color = '#27ae60' if status == '营业中' else ('#f39c12' if status == '即将营业' else '#e74c3c')

        taste = str(detail.get('口味', '') or '')
        env = str(detail.get('环境', '') or '')
        service = str(detail.get('服务', '') or '')
        rank = str(detail.get('榜单', '') or '')
        note = str(detail.get('备注', '') or '')
        hours = str(detail.get('营业时间', '') or '')
        price = str(detail.get('人均', '') or '')

        popup_html = (
            '<div style="font-family:\'PingFang SC\',\'Microsoft YaHei\',sans-serif;width:290px">'
            '<div style="font-size:14px;font-weight:bold;color:#2c3e50;margin-bottom:8px;'
            'border-bottom:3px solid ' + color + ';padding-bottom:8px">'
            '<span style="color:' + color + ';font-size:16px">[' + str(sid) + ']</span> ' + name
        )
        popup_html += (
            '</div>'
            '<table style="font-size:12px;width:100%;border-collapse:collapse">'
            '<tr><td style="padding:3px 0;color:#95a5a6;width:48px">📍</td>'
            '<td style="padding:3px 0;color:#2c3e50">' + addr + '</td></tr>'
            '<tr><td style="padding:3px 0;color:#95a5a6">状态</td>'
            '<td style="padding:3px 0;color:' + status_color + ';font-weight:600">'
            + status_icon + ' ' + status + '</td></tr>'
        )
        if hours:
            popup_html += '<tr><td style="padding:3px 0;color:#95a5a6">营业</td><td style="padding:3px 0;color:#555">' + hours + '</td></tr>'
        if price:
            popup_html += '<tr><td style="padding:3px 0;color:#95a5a6">人均</td><td style="padding:3px 0;color:#e67e22;font-weight:600">¥' + price + ' 元</td></tr>'
        if taste:
            popup_html += '<tr><td style="padding:3px 0;color:#95a5a6">评分</td><td style="padding:3px 0">🍖 ' + taste + ' &nbsp;🏠 ' + env + ' &nbsp;🙋 ' + service + '</td></tr>'
        if rank:
            popup_html += '<tr><td style="padding:3px 0;color:#95a5a6">榜单</td><td style="padding:3px 0;color:#8e44ad;font-size:11px">' + rank + '</td></tr>'
        if note:
            popup_html += '<tr><td style="padding:3px 0;color:#95a5a6">备注</td><td style="padding:3px 0;color:#7f8c8d;font-size:11px">' + note + '</td></tr>'
        popup_html += (
            '</table>'
            '<div style="margin-top:6px;font-size:10px;color:#bdc3c7;text-align:right">'
            'WGS-84: ' + str(lat)[:8] + ', ' + str(lng)[:8]
            + '</div></div>'
        )

        folium.Marker(
            location=[lat, lng],
            popup=folium.Popup(popup_html, max_width=310),
            tooltip=f"[{sid}] {name} · {region}",
            icon=folium.DivIcon(
                html='<div style="width:32px;height:32px;border-radius:50% 50% 50% 0;'
                     'background:' + color + ';border:3px solid white;'
                     'box-shadow:0 2px 6px rgba(0,0,0,0.35);transform:rotate(-45deg);'
                     'display:flex;align-items:center;justify-content:center">'
                     '<span style="transform:rotate(45deg);color:white;font-size:12px;font-weight:bold">'
                     + str(sid) + '</span></div>',
                icon_size=(32, 32),
                icon_anchor=(16, 32),
                popup_anchor=(0, -34),
            ),
        ).add_to(m)

    # 标题
    title_html = (
        '<div style="position:fixed;top:12px;left:50%;transform:translateX(-50%);'
        'background:#2c3e50;color:white;padding:10px 28px;border-radius:24px;'
        'font-size:14px;font-weight:bold;z-index:9999;box-shadow:0 4px 14px rgba(0,0,0,0.25);'
        'font-family:\'PingFang SC\',\'Microsoft YaHei\',sans-serif;white-space:nowrap;'
        'border:1px solid rgba(255,255,255,0.1)">'
        '🗺️ 食为先·竞品门店分布地图 <span style="color:#ffd700">('
        + str(len(coords)) + '/37 家）</span></div>'
    )
    m.get_root().html.add_child(folium.Element(title_html))

    # 图例
    legend_items = ''
    for r, c in REGION_COLORS.items():
        cnt = len(region_groups.get(r, []))
        if cnt > 0:
            legend_items += (
                '<span style="display:inline-block;width:13px;height:13px;'
                'border-radius:50%;background:' + c + ';margin-right:7px"></span>'
                + r + ' (' + str(cnt) + ')<br>'
            )
    legend_html = (
        '<div style="position:fixed;bottom:28px;right:18px;'
        'background:rgba(255,255,255,0.97);padding:14px 18px;border-radius:12px;'
        'box-shadow:0 4px 14px rgba(0,0,0,0.15);font-size:12px;z-index:9999;line-height:2.1;'
        'font-family:\'PingFang SC\',\'Microsoft YaHei\',sans-serif;'
        'border:1px solid rgba(0,0,0,0.08)">'
        '<div style="font-size:13px;font-weight:bold;color:#2c3e50;margin-bottom:6px;'
        'border-bottom:1px solid #eee;padding-bottom:6px">📍 区域图例</div>'
        + legend_items + '</div>'
    )
    m.get_root().html.add_child(folium.Element(legend_html))

    # 统计面板
    open_count = sum(1 for s in coords.values() if s["status"] == "营业中")
    soon_count = sum(1 for s in coords.values() if s["status"] == "即将营业")
    other_count = sum(1 for s in coords.values() if s["status"] not in ["营业中", "即将营业"])
    stat_html = (
        '<div style="position:fixed;top:60px;right:18px;'
        'background:rgba(255,255,255,0.97);padding:12px 16px;border-radius:12px;'
        'box-shadow:0 4px 14px rgba(0,0,0,0.12);font-size:12px;z-index:9999;line-height:1.9;'
        'font-family:\'PingFang SC\',\'Microsoft YaHei\',sans-serif;'
        'border:1px solid rgba(0,0,0,0.08);min-width:140px">'
        '<div style="font-size:12px;font-weight:bold;color:#2c3e50;margin-bottom:4px">📊 门店统计</div>'
        '<div style="color:#27ae60">🟢 营业中: ' + str(open_count) + '</div>'
        '<div style="color:#f39c12">🟡 即将营业: ' + str(soon_count) + '</div>'
        '<div style="color:#e74c3c">🔴 其他: ' + str(other_count) + '</div>'
        '</div>'
    )
    m.get_root().html.add_child(folium.Element(stat_html))

    # 图层控制
    folium.LayerControl(collapsed=False).add_to(m)

    output = 'shop_map_final.html'
    m.save(output)
    print(f"✅ 地图已生成: {output}")
    return output


if __name__ == '__main__':
    generate_map()
