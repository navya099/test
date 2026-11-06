"""실행 진입점."""
import platform

from matplotlib import pyplot as plt

from ui.app import TunnelApp

# 운영체제별 기본 한글 폰트 설정
if platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
elif platform.system() == 'Darwin':  # macOS
    plt.rc('font', family='AppleGothic')
else:  # Linux 등
    plt.rc('font', family='NanumGothic')

# 마이너스 기호(-) 깨짐 현상 방지
plt.rcParams['axes.unicode_minus'] = False
if __name__ == "__main__":
    TunnelApp().run()