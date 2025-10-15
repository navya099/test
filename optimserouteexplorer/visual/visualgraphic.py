from folium import folium
import json
from core.util import haversine

def visualize_routes_with_button(alignments, start, end, top_n=5, map_file="candidate_routes.html"):
    center = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2]

    m = folium.Map(location=center, zoom_start=7)
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'darkred', 'cadetblue']

    # Chart.js용 canvas
    chart_div = """
    <canvas id="profile_canvas" style="width:100%; height:300px;"></canvas>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
window.profileChart = null;

function showProfile(planElevs, groundElevs, distances){
    // canvas와 실제 픽셀 크기 조정
    var canvas = document.getElementById('profile_canvas');
    canvas.width = canvas.offsetWidth * window.devicePixelRatio;
    canvas.height = canvas.offsetHeight * window.devicePixelRatio;

    var ctx = canvas.getContext('2d');

    if(window.profileChart) window.profileChart.destroy();

    var planData = planElevs.map(([sta, elev]) => ({ x: sta, y: elev }));
    var groundData = groundElevs.map((e,i)=>({x: distances[i], y: e}));

    window.profileChart = new Chart(ctx,{
        type:'line',
        data:{datasets:[
            {label:'Plan', data:planData, borderColor:'red', fill:false},
            {label:'Ground', data:groundData, borderColor:'blue', fill:false}
        ]},
        options:{
            responsive:false,
            maintainAspectRatio:false,
            plugins:{legend:{display:true}},
            scales:{
                x:{
                    type:'linear',
                    position:'bottom',
                    title:{display:true, text:'Distance (km)'}
                },
                y:{
                    title:{display:true, text:'Elevation (m)'}
                }
            }
        }
    });
}
</script>

    """

    m.get_root().html.add_child(folium.Element(chart_div))

    for idx, alignment in enumerate(alignments[:top_n]):
        color = colors[idx % len(colors)]

        # elevations
        plan_elevs = [(sta / 1000, fl) for sta, fl in alignment.fls]
        ground_elevs = alignment.grounds

        # 누적 거리(km) 계산
        distances = [0]
        for i in range(1, len(alignment.coords)):
            distances.append(distances[-1] + haversine(alignment.coords[i - 1], alignment.coords[i]) / 1000)  # km 단위


        plan_json = json.dumps(plan_elevs)
        ground_json = json.dumps(ground_elevs)
        dist_json = json.dumps(distances)

        # 팝업 HTML
        popup_html = f"""
        ID: {idx} <br>
        Length:{alignment.length:.2f}
        Cost: {alignment.cost:.1f} <br>
        Bridge: {alignment.total_bridge_length:.1f}m <br>
        Tunnel: {alignment.total_tunnel_length:.1f}m <br>
        <button onclick='showProfile({plan_json}, {ground_json}, {dist_json})'>View Profile</button>
        """
        polyline = folium.PolyLine(
            locations=alignment.coords,
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