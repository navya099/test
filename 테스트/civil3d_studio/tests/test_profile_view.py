import tkinter as tk

from profile.profile_engine import Civil3DProfileEngine
from profile.pvi import PVIPoint
from profile_view.profile_view import Civil3DProfileViewerApp

# 1. 리스트 대괄호 [...]로 올바르게 묶어줍니다.
pvis = [
    PVIPoint("BVP", station=1000.0, elevation=50.0),
    PVIPoint("PVI-1", station=1500.0, elevation=75.0, L=200.0),             # 대칭 볼록 (Crest): L=200m
    PVIPoint("PVI-2", station=2100.0, elevation=60.0, L1=100.0, L2=150.0),  # 비대칭 오목 (Sag): L1=100m, L2=150m
    PVIPoint("EVP", station=2600.0, elevation=85.0)
]

# 2. build 메서드는 @staticmethod이므로 클래스명으로 직접 호출하거나 인스턴스를 통해 호출 가능
profile = Civil3DProfileEngine.build(name="본선_계획종단_FG", pvi_list=pvis)
profile.print_profile_report()

root = tk.Tk()
app = Civil3DProfileViewerApp(root, profile)
root.mainloop()