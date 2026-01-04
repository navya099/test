import math
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt

from math_utils import calculate_distance, calculate_bearing


class TangentSolver:
    def __init__(self, A, C, R):
        """
        A: 외부 점 (tuple, ex: (x, y))
        C: 원 중심 (tuple, ex: (x, y))
        R: 반지름 (float)
        """
        self.A = A
        self.C = C
        self.R = R

    def tangent_points(self):
        """외부 점 A에서 원에 접하는 두 접점 좌표를 반환"""
        xa, ya = self.A
        xc, yc = self.C
        x, y = sp.symbols('x y', real=True)

        eq1 = (x - xc)**2 + (y - yc)**2 - self.R**2
        eq2 = (x - xc)*(xa - x) + (y - yc)*(ya - y)

        sol = sp.solve([eq1, eq2], (x, y))
        return [(float(px), float(py)) for px, py in sol]

    def top_point(self, points):
        """y 좌표가 큰 접점을 반환 (위쪽 점)"""
        return max(points, key=lambda p: p[1])

    def visualize(self, points, top_point=None):
        """원, 점 A, 중심 C, 접점, 접선 시각화"""
        fig, ax = plt.subplots(figsize=(6,6))
        ax.set_aspect('equal')
        ax.grid(True)

        # 원
        circle = plt.Circle(self.C, self.R, fill=False, color='black', linestyle='--')
        ax.add_artist(circle)

        # 점 A, C
        ax.scatter(*self.A, color='blue')
        ax.text(self.A[0]+0.05, self.A[1], 'A', color='blue')

        ax.scatter(*self.C, color='red')
        ax.text(self.C[0]+0.05, self.C[1], 'C', color='red')

        # 접점 및 접선
        for i, P in enumerate(points):
            ax.scatter(*P, color='green')
            ax.text(P[0]+0.05, P[1], f'T{i+1}', color='green')
            ax.plot([self.A[0], P[0]], [self.A[1], P[1]], color='orange', label=f'Tangent {i+1}' if i==0 else None)

        if top_point:
            ax.plot([self.A[0], top_point[0]], [self.A[1], top_point[1]], 'r--', label='Top tangent')

        ax.legend()
        ax.set_title("Circle with tangent lines from A")
        plt.tight_layout()
        plt.show()

if __name__ == '__main__':
    # 모듈 사용
    A = (-2.947, 5.136)
    C = (0.2, 6.570)
    R = 0.11

    solver = TangentSolver(A, C, R)

    points = solver.tangent_points()

    top_point = solver.top_point(points)
    angle = calculate_bearing(A, top_point)
    length= calculate_distance(A, top_point) + 0.15
    print("경사 주 파이프 각도:", math.degrees(angle))
    print("경사 주 파이프 길이:", length)