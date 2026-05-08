class TextLayoutService:
    """텍스트 좌표 계산 서비스"""
    @staticmethod
    def calculate_position(station: str, curvetype: str):
        text_parts = station.split('.')
        digit = len(text_parts[0]) if len(text_parts) == 2 else 0

        if digit == 1:
            cooradjust = 20
        elif digit == 2:
            cooradjust = 0
        elif digit == 3:
            cooradjust = -10
        else:
            cooradjust = 0

        if curvetype in ['PC', 'CP', 'BC', 'EC']:
            x, y = 121 + cooradjust, 92
        else:
            x, y = 121 + cooradjust, 115

        return x * 2.83465, y * 2.83465  # mm → pt 변환
