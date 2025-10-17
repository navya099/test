import pandas as pd

def export_excel_report(top10, save_file):
    # 엑셀로 저장할 때 필요한 키만 선택
    excel_keys = [
        "ID",
        "노선연장",
        "공사비",
        "교량갯수",
        "터널갯수",
        "곡선갯수",
        "기울기갯수",
        "최급기울기",
        "최소곡선반경"
    ]

    # top10은 그대로 두고, 엑셀용 데이터만 새로 만듦
    excel_data = [{k: entry[k] for k in excel_keys} for entry in top10]

    # 엑셀 저장
    df = pd.DataFrame(excel_data)
    df.to_excel(save_file, index=False)
    print("Excel 저장 완료 GA!")