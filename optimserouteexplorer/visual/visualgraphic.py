import folium
import json

def visualize_routes_with_button(alignments, start, end, top_n=5, map_file='map.html'):
    center = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2]
    m = folium.Map(location=center, zoom_start=7)
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'darkred', 'cadetblue']

    chart_div = """
    <canvas id="profile_canvas" style="width:100%; height:300px;"></canvas>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="profile.js"></script>
    """
    m.get_root().html.add_child(folium.Element(chart_div))

    for idx, alignment in enumerate(alignments[:top_n]):
        base_color = colors[idx % len(colors)]

        plan_json = json.dumps(alignment['fls'])
        ground_json = json.dumps(alignment['grounds'])

        popup_html = f"""
        ID: {alignment['ID']} <br>
        Length: {alignment['노선연장']:.2f} km<br>
        Cost: {alignment['공사비']:.1f} <br>
        Bridge Count: {alignment['교량갯수']}<br>
        Tunnel Count: {alignment['터널갯수']}<br>
        <button onclick='showProfile({plan_json}, {ground_json})'>View Profile</button>
        """

        # ✅ 노선별 그룹 생성
        route_group = folium.FeatureGroup(name=f"노선 {alignment['ID']}")

        coords = alignment['coords']
        stations = alignment['station_list']
        structures = alignment['collections']

        segment = []
        current_type = structures.get_structure_type_at(stations[0])

        for i, coord in enumerate(coords):
            segment.append(coord)
            next_type = structures.get_structure_type_at(stations[i + 1]) if i < len(stations) - 1 else None
            structure = structures.find_containing(stations[i])

            if i == len(coords)-1 or next_type != current_type:
                if current_type == "교량":
                    seg_color = "pink"
                    seg_weight = 12
                    seg_popup = f"노선번호:{alignment['ID']}<br> {structure.name},L={structure.length}m"
                elif current_type == "터널":
                    seg_color = "yellow"
                    seg_weight = 12
                    seg_popup = f"노선번호:{alignment['ID']}<br> {structure.name},L={structure.length}m"
                else:
                    seg_color = base_color
                    seg_weight = 6
                    seg_popup = popup_html

                seg_line = folium.PolyLine(
                    locations=segment,
                    color=seg_color,
                    weight=seg_weight,
                    opacity=1,
                    popup=seg_popup,
                )
                seg_line.add_to(route_group)

                segment = []
                current_type = next_type

        # CircleMarker (간격 표시)
        for i, coord in enumerate(coords):
            if i % 8 == 0:
                sta = stations[i] if 'station_list' in alignment else i
                structure = structures.get_structure_type_at(sta)
                point_popup = folium.Popup(f"노선번호:{alignment['ID']}, STA: {sta}<br>Structure: {structure}", max_width=200)
                folium.CircleMarker(
                    location=coord,
                    radius=3,
                    color=base_color,
                    fill=True,
                    fill_opacity=0.8,
                    popup=point_popup
                ).add_to(route_group)

        route_group.add_to(m)

    # 시작/끝 마커
    folium.Marker(location=start, popup="Start", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker(location=end, popup="End", icon=folium.Icon(color='red')).add_to(m)

    # ✅ LayerControl 추가 (체크박스 UI)
    folium.LayerControl(collapsed=False).add_to(m)

    m.save(map_file)
    print(f"지도 시각화 파일({map_file})이 생성되었습니다.")