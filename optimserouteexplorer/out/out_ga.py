def format_top10(population, top_n=10) -> list[dict]:
    """
    GA 최종 후보를 웹/엑셀용 dict 포맷으로 변환
    """
    top10 = []
    for i, cand in enumerate(population[:top_n]):
        # plan_full과 profile 생성
        plan_full = cand['plan_full']
        profile = cand['profile']
        result = cand['result']
        radius_list = cand['radius_list']
        top10.append({
            "ID": i,
            "노선연장": plan_full['linestring'].length,
            "공사비": round(cand['cost'], 1),
            "교량갯수": len(result.get('bridges', 0)),
            "터널갯수": len(result.get('tunnels', 0)),
            "곡선갯수": len(radius_list),
            "기울기갯수": len(profile.get('slopes', 0)),
            "최급기울기": max(profile.get('slopes', 0)) * 1000,
            "최소곡선반경": min(radius_list),
            "coords": [[c[1], c[0]] for c in plan_full['wgs_coords']],
            "fls": profile.get('fg_profile'),  # 필요 시 profile에서 채움
            "grounds": profile.get('eg_profile')
        })
    return top10