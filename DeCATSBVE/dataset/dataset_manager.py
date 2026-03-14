import json

def load_dataset(designspeed, iscustommode):
    if iscustommode:
        filename = r'c:/temp/custom_data.json'
        xlsxname = r'c:/temp/custom_spandata.xlsx'
    else:
        if designspeed == 150:
            filename = r'c:/temp/railway_150.json'
            xlsxname = r'c:/temp/spandata_150.xlsx'
        elif designspeed == 250:
            filename = r'c:/temp/railway_250.json'
            xlsxname = r'c:/temp/spandata_250.xlsx'
        elif designspeed == 350:
            filename = r'c:/temp/railway_350.json'
            xlsxname = r'c:/temp/spandata_350.xlsx'
        else:
            raise ValueError(f'지원하지 않는 속도 모드입니다. {designspeed}')
    with open(filename, "r", encoding="utf-8") as f:
        base_data = json.load(f)
    import pandas as pd
    # 모든 시트를 읽어서 구조화
    sheets = pd.read_excel(xlsxname, sheet_name=None)

    span_data = {}
    for sheet_name, df in sheets.items():
        # 각 시트별로 {길이: 인덱스} 구조화
        span_data[sheet_name] = dict(zip(df['길이'], df['인덱스']))

    base_data['span_data'] = span_data
    return base_data