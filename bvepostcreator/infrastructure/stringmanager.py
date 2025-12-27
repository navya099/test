class StringManager:
    def __init__(self):
        pass

    @staticmethod
    def resize_to_length(text, desired_length=1):
        """
        문자열의 길이가 원하는 길이와 다를 경우 강제로 조정합니다.
        기본적으로 원하는 길이는 1로 설정되어 있습니다.

        Parameters:
        text (str): 입력 문자열
        desired_length (int): 원하는 문자열 길이 (기본값: 1)

        Returns:
        str: 조정된 문자열
        """
        if len(text) != desired_length:
            # 문자열을 원하는 길이로 자르거나, 부족한 경우 앞에 '0'을 채웁니다.
            if len(text) > desired_length:
                return text[:desired_length]
            else:
                return text.zfill(desired_length)
        return text