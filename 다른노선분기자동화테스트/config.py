# config.py

MAIN_TRACK_NAME = '자선'

# 건넘선 설계 조건 (로컬 테스트용 하드코딩)
BRANCH_START_STATION = 59375
BRANCH_END_STATION = 59575
BRANCH_TARGET_TRACK = 28
TRACK_OFFSET_X = 7.0       # 트랙 횡거리 (m) - 타선 파일 대신 이 값을 사용
BRANCH_LENGTH = 100      # 건넘선 설치 길이 (m)

# 설계 제약조건 (25m 호, 12.5m 직선)
CURVE_UNIT = 50
STRAIGHT_UNIT = 12.5

# 목표 반지름 (최적해 탐색 시 사용)
TARGET_RADIUS = 360.0
MIN_RADIUS = 250.0