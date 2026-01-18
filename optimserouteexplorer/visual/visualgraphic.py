import folium
import json

def visualize_routes_with_button(alignments, start, end, top_n=5, map_file=''):
    center = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2]

    m = folium.Map(location=center, zoom_start=7)
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'darkred', 'cadetblue']

    # Chart.js용 canvas
    chart_div = """
    <canvas id="profile_canvas" style="width:100%; height:300px;"></canvas>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="profile.js"></script>
    """

    m.get_root().html.add_child(folium.Element(chart_div))

    for idx, alignment in enumerate(alignments[:top_n]):
        color = colors[idx % len(colors)]

        # elevations
        plan_elevs = alignment['fls']

        ground_elevs = alignment['grounds']

        plan_json = json.dumps(plan_elevs)
        ground_json = json.dumps(ground_elevs)

        #팝업 html
        popup_html = f"""
        ID: {alignment['ID']} <br>
        Length: {alignment['노선연장']:.2f} km<br>
        Cost: {alignment['공사비']:.1f} <br>
        Bridge Count: {alignment['교량갯수']}<br>
        Tunnel Count: {alignment['터널갯수']}<br>
        <button onclick='showProfile({plan_json}, {ground_json})'>View Profile</button>
        """
        polyline = folium.PolyLine(
            locations=alignment['coords'],
            color=color,
            weight=5,
            opacity=0.7,
        )
        polyline.add_child(folium.Popup(popup_html, max_width=300))
        polyline.add_to(m)

    folium.Marker(location=start, popup="Start", icon=folium.Icon(color='green')).add_to(m)
    folium.Marker(location=end, popup="End", icon=folium.Icon(color='red')).add_to(m)

    m.save(map_file)
    print(f"지도 시각화 파일({map_file})이 생성되었습니다.")