from model.grade.vipdata import VIPdata


def calculate_vertical_curve_radius(length: float, start_grade: float, end_grade: float) -> float:
    """
    종곡선 반지름(R)을 계산하는 함수

    Parameters:
        length (float): 종곡선 길이 (L), 단위: m
        start_grade (float): 시작 경사, 단위: m/m (예: -0.025 for -25‰)
        end_grade (float): 끝 경사, 단위: m/m

    Returns:
        float: 종곡선 반지름 R (단위: m)
    """
    delta_g = end_grade - start_grade  # 경사 변화량 (m/m)

    if delta_g == 0:
        return 0.0  # 구배 변화가 없으면 반지름은 무한대 (직선)

    radius = length / abs(delta_g)  # 반지름 계산 (단위: m)
    return radius

def get_vertical_curve_type(start_grade: float, end_grade: float) -> str:
    if start_grade > end_grade:
        return "볼록형"  # 볼록형 (정상 곡선)
    else:
        return "오목형"  # 오목형 (골짜기 곡선)

# 1. 곡선 구간(Line) 생성 분리
def get_vcurve_lines(vip: VIPdata) -> list[list]:
    if vip.isvcurve:
        return [['BVC', vip.BVC_STA], ['VIP', vip.VIP_STA], ['EVC', vip.EVC_STA]]
    else:
        return [['VIP', vip.VIP_STA]]

def format_grade(value):
    """
    구배를 1000곱하고 변환 포맷
    """
    return f"{value * 1000:.1f}".rstrip('0').rstrip('.')  # 소수점 이하 0 제거