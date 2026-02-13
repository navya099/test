import json

def load_dataset(designspeed, iscustommode):
    if iscustommode:
        filename = r'c:/temp/custom_data.json'
    else:
        if designspeed == 150:
            filename = r'c:/temp/railway_150.json'
        elif designspeed == 250:
            filename = r'c:/temp/railway_250.json'
        elif designspeed == 350:
            filename = r'c:/temp/railway_350.json'
        else:
            raise ValueError(f'지원하지 않는 속도 모드입니다. {designspeed}')
    with open(filename, "r", encoding="utf-8") as f:
        base_data = json.load(f)
    return base_data