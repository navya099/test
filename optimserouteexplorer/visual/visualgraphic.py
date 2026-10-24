# visual/visualgraphic.py
"""
GA 결과를 folium 지도로 시각화 (로컬 전용).

- alignments: format_top10 출력 (dict 기반)
- collections: list[dict] (station 별 구조 요약)
- map_file: 생성될 HTML 파일 경로 (로컬 전용)
"""
import json
import logging

import folium

logger = logging.getLogger(__name__)

_COLORS = ["red", "blue", "green", "orange", "purple", "darkred", "cadetblue"]


def visualize_routes_with_button(alignments, start, end, top_n=5, map_file="map.html"):
    if not alignments:
        logger.warning("시각화할 후보가 없습니다")
        return

    center = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2]
    m = folium.Map(location=center, zoom_start=7)

    chart_div = """
    <canvas id="profile_canvas" style="width:100%; height:300px;"></canvas>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="profile.js"></script>
    """
    m.get_root().html.add_child(folium.Element(chart_div))

    for idx, alignment in enumerate(alignments[:top_n]):
        base_color = _COLORS[idx % len(_COLORS)]

        plan_json = json.dumps(alignment.get("fls"))
        ground_json = json.dumps(alignment.get("grounds"))

        popup_html = f"""
        ID: {alignment.get('ID')} <br>
        Length: {_fmt(alignment.get('노선연장'), '.2f')} km<br>
        Cost: {_fmt(alignment.get('공사비'), '.1f')} <br>
        Bridge Count: {alignment.get('교량갯수', 0)}<br>
        Tunnel Count: {alignment.get('터널갯수', 0)}<br>
        <button onclick='showProfile({plan_json}, {ground_json})'>View Profile</button>
        """

        route_group = folium.FeatureGroup(name=f"노선 {alignment.get('ID')}")

        coords = alignment.get("coords", [])
        stations = alignment.get("station_list", [])
        structures = alignment.get("collections", [])   # list[dict]

        def type_at(i: int):
            return structures[i].get("type") if 0 <= i < len(structures) else None

        def structure_at(i: int) -> dict:
            if 0 <= i < len(structures):
                return structures[i]
            return {"name": None, "length": 0.0}

        if not coords:
            route_group.add_to(m)
            continue

        segment = []
        current_type = type_at(0)

        for i, coord in enumerate(coords):
            segment.append(coord)
            next_type = type_at(i + 1) if i < len(stations) - 1 else None
            structure = structure_at(i)

            if i == len(coords) - 1 or next_type != current_type:
                if current_type == "교량":
                    seg_color, seg_weight = "pink", 12
                    seg_popup = (
                        f"노선번호:{alignment.get('ID')}<br> "
                        f"{structure.get('name')},L={structure.get('length')}m"
                    )
                elif current_type == "터널":
                    seg_color, seg_weight = "yellow", 12
                    seg_popup = (
                        f"노선번호:{alignment.get('ID')}<br> "
                        f"{structure.get('name')},L={structure.get('length')}m"
                    )
                else:
                    seg_color, seg_weight = base_color, 6
                    seg_popup = popup_html

                folium.PolyLine(
                    locations=segment,
                    color=seg_color,
                    weight=seg_weight,
                    opacity=1,
                    popup=seg_popup,
                ).add_to(route_group)

                segment = []
                current_type = next_type

        # CircleMarker
        for i, coord in enumerate(coords):
            if i % 8 == 0:
                sta = stations[i] if i < len(stations) else i
                stype = type_at(i)
                point_popup = folium.Popup(
                    f"노선번호:{alignment.get('ID')}, STA: {sta}<br>Structure: {stype}",
                    max_width=200,
                )
                folium.CircleMarker(
                    location=coord,
                    radius=3,
                    color=base_color,
                    fill=True,
                    fill_opacity=0.8,
                    popup=point_popup,
                ).add_to(route_group)

        route_group.add_to(m)

    folium.Marker(location=start, popup="Start",
                  icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(location=end, popup="End",
                  icon=folium.Icon(color="red")).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    m.save(map_file)
    logger.info("지도 시각화 파일(%s) 생성", map_file)


def _fmt(v, fmt: str) -> str:
    if v is None:
        return "-"
    try:
        return format(float(v), fmt)
    except (TypeError, ValueError):
        return str(v)