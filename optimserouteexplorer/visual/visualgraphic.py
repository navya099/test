import folium
import json

def visualize_routes_with_button(alignments, start, end, top_n=5, map_file='map.html'):
    center = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2]
    m = folium.Map(location=center, zoom_start=7)
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'darkred', 'cadetblue']

    # Chart.js용 canvas + 외부 스크립트
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

        # 노선 팝업
        popup_html = f"""
        ID: {alignment['ID']} <br>
        Length: {alignment['노선연장']:.2f} km<br>
        Cost: {alignment['공사비']:.1f} <br>
        Bridge Count: {alignment['교량갯수']}<br>
        Tunnel Count: {alignment['터널갯수']}<br>
        <button onclick='showProfile({plan_json}, {ground_json})'>View Profile</button>
        """

        # -------------------------------
        # 구간별 PolyLine (구조물 여부에 따라 색상/굵기 변경)
        # -------------------------------
        coords = alignment['coords']
        stations = alignment['station_list']
        structures = alignment['collections']  # 구조물 판정 객체

        segment = []
        current_type = structures.get_structure_type_at(stations[0])

        for i, coord in enumerate(coords):
            segment.append(coord)
            next_type = structures.get_structure_type_at(stations[i + 1]) if i < len(stations) - 1 else None

            # 구조물 타입이 바뀌거나 마지막 점이면 PolyLine 생성
            if i == len(coords)-1 or next_type != current_type:
                if current_type == "교량":
                    seg_color = "skyblue"
                    seg_weight = 12
                elif current_type == "터널":
                    seg_color = "pink"
                    seg_weight = 12
                else:
                    seg_color = base_color
                    seg_weight = 6

                seg_line = folium.PolyLine(
                    locations=segment,
                    color=seg_color,
                    weight=seg_weight,
                    opacity=0.8,
                    popup=popup_html,
                )
                seg_line.add_to(m)

                # 다음 구간 초기화
                segment = []
                current_type = next_type

        # -------------------------------
        # 각 점에 CircleMarker 추가 (STA와 구조물 여부 표시)
        # -------------------------------
        for i, coord in enumerate(coords):
            if i % 8 == 0:  # 8번째 점마다만 표시(200m간격)
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
                ).add_to(m)

    # 시작/끝 마커
    folium.Marker(location=start, popup="Start", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker(location=end, popup="End", icon=folium.Icon(color='red')).add_to(m)

    # 저장
    m.save(map_file)
    print(f"지도 시각화 파일({map_file})이 생성되었습니다.")