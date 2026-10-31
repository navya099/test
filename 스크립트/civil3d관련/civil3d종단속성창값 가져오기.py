from tkinter.filedialog import askopenfilename, askdirectory
from pathlib import Path
import pandas as pd
import re


def station_to_float(station):
    """
    0+113.72m -> 113.72
    1+234.56m -> 1234.56
    """
    station = str(station).replace("m", "").strip()

    if "+" in station:
        km, m = station.split("+")
        return float(km) * 1000 + float(m)

    return float(station)


def read_xlsx(file_path):
    df = pd.read_excel(file_path, engine="openpyxl")

    profile_points = {}
    vertical_curves = {}

    for sta, elev, vc in zip(
        df["PVI 측점"],
        df["PVI 표고"],
        df["종단 원곡선 길이"]
    ):
        if pd.isna(sta) or pd.isna(elev):
            continue

        sta_value = round(station_to_float(sta), 3)

        elev_value = float(
            str(elev).replace("m", "").strip()
        )

        profile_points[sta_value] = elev_value

        if not pd.isna(vc):
            vc_length = float(vc)

            if vc_length > 0:
                vertical_curves[str(sta_value)] = vc_length

    profile_points = [
        [sta, elev]
        for sta, elev in sorted(profile_points.items())
    ]

    return profile_points, vertical_curves


import json


def combine_profile_config(datas, config_path):
    plan_data, ground_data = datas

    config = {
        "plan_points": plan_data,
        "ground_points": ground_data
    }

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(
            config,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(f"PROFILE 저장 완료 : {config_path}")

def create_vertical_curve_config(config_path, data):
    """종곡선 정보 json 생성기
    양식:

{
  "1389.5": 300
}

    """
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False
        )

def main():
    file_dir = askdirectory(title="종단선형 엑셀 폴더 선택")

    if not file_dir:
        raise FileNotFoundError("폴더를 선택하지 않았습니다.")

    import os
    config_path = os.path.join(file_dir, "profile_test_config.json")

    #1 종단파일
    plan_profile_filename = r'배치종단속성편집테이블.xlsx'
    ground_profile_filename = r'지표면종단속성편집테이블.xlsx'
    plan_path = os.path.join(file_dir, plan_profile_filename)
    ground_path = os.path.join(file_dir, ground_profile_filename)

    #새 json 작성
    plan_coordinates, vertical_curves = read_xlsx(plan_path)
    ground_coordinates, _ = read_xlsx(ground_path)

    combine_profile_config(
        [plan_coordinates, ground_coordinates],
        config_path
    )

    #2 종곡선 정보파일
    #종곡선 정보 json 생성
    vertical_config_path = os.path.join(file_dir, "vertical-curve-simple.json")

    create_vertical_curve_config(
        vertical_config_path,
        vertical_curves
    )

if __name__ == "__main__":
    main()