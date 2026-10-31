from tkinter import Tk
from tkinter.filedialog import askdirectory
from pathlib import Path


def main():
    root = Tk()
    root.withdraw()

    project_dir = Path(
        askdirectory(title="준공도 폴더 선택")
    )

    if not project_dir:
        return

    cmd = (
        f'python combined_plan_profile_v1_8a.py '
        f'--plan "{project_dir / "본선평면선형.dxf"}" '
        f'--profile "{project_dir / "test_profile.dxf"}" '
        f'--sheet-length 700 '
        f'--horizontal-scale 1000 '
        f'--vertical-scale 400 '
        f'--start-sta 0 '
        f'--end-sta 88000 '
        f'--titleblock-config "{project_dir / "titleblock_config.json"}" '
        f'--output-dir "{project_dir / "종평면도"}" '
        f'--left-direction "함열쪽" '
        f'--right-direction "천안쪽" '
        f'--vertical-curve-sta-json "{project_dir / "vertical-curve-simple.json"}" '
        f'--structures-csv "{project_dir / "structure_segments.csv"}" '
        f'--structure-settings-json "{project_dir / "structure_settings_B8_example.json"}" '
    )

    root.clipboard_clear()
    root.clipboard_append(cmd)
    root.update()

    print("=" * 60)
    print("명령어가 클립보드에 복사되었습니다.")
    print("=" * 60)
    print(cmd)


if __name__ == "__main__":
    main()