import numpy as np
import matplotlib.pyplot as plt

def sag_parabola(L, w, T):
    # 중앙 이도 공식
    f = (w * L**2) / (8 * T)
    print(f"전선 길이: {L}m, 단위중량: {w}kg/m, 장력 {T}N")
    print(f"중앙 이도: {f:.3f} m")
    return f

def plot_catenary(L, w, T, f, step=0.5, mark_x=None):
    # 포물선 근사 곡선 (아래 방향으로)
    xs = np.arange(0, L+step, step)
    ys = [-4*f/(L**2) * x * (L - x) for x in xs]

    # 그래프 시각화
    plt.figure(figsize=(8,4))
    plt.plot(xs, ys, label="Sag curve (parabola)")
    plt.scatter([L/2], [-f], color="red", label="중앙 이도")

    # 특정 x점 표시
    if mark_x is not None:
        y_val = -4*f/(L**2) * mark_x * (L - mark_x)
        plt.scatter([mark_x], [y_val], color="blue", label=f"x={mark_x}m")
        print(f"x={mark_x}m 에서 y={y_val:.3f} m")

    plt.title("전선 이도 곡선 (근사식)")
    plt.xlabel("x (m)")
    plt.ylabel("y (m)")
    plt.legend()
    plt.grid(True)
    plt.show()

def main():
    # 예시 실행
    f = sag_parabola(L=13, w=1.5, T=800)
    plot_catenary(L=13, w=1.5, T=800, f=f, step=0.5, mark_x=None)

if __name__ == "__main__":
    main()