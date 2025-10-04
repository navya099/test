import os

from filemanager import FileManager
from library import LibraryManager

class PoleAssemblerCLI:
    def __init__(self):
        self.lib_manager = LibraryManager()
        self.lib_manager.scan_library()
        self.selections = {}
        self.gauge = 0
        self.output = ""

    def select_from_list(self, prompt, options):
        """숫자 메뉴로 선택"""
        print(prompt)
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        while True:
            try:
                choice = int(input("번호 선택: "))
                if 1 <= choice <= len(options):
                    return options[choice-1]
            except ValueError:
                pass
            print("잘못된 입력입니다. 다시 선택해주세요.")

    def run(self):
        # 1. 선로 선택
        rail_options = ['도시철도', '일반철도', '고속철도', '준고속철도']
        self.railtype = self.select_from_list("선로 종류 선택:", rail_options)

        #그룹매핑
        group = self.lib_manager.define_group(self.railtype)
        # 2. 전주 선택
        pole_files = self.lib_manager.list_files_in_category('기둥', group='base')
        self.selections["기둥"] = self.select_from_list("전주 파일 선택:", pole_files)

        # 3. 브래킷 선택
        bracket_files = self.lib_manager.list_files_in_category(category='브래킷',group=group)
        self.selections["브래킷"] = self.select_from_list("브래킷 파일 선택:", bracket_files)

        # 4. 급전선 선택
        feeder_files = self.lib_manager.list_files_in_category('급전선설비', group='base')
        self.selections["급전선설비"] = self.select_from_list("급전선 파일 선택:", feeder_files)

        # 5. 보호선 선택
        fpw_files = self.lib_manager.list_files_in_category('금구류', group='base')
        self.selections["금구류"] = self.select_from_list("보호선 파일 선택:", fpw_files)

        # 6. 건식게이지
        while True:
            try:
                self.gauge = float(input("건식게이지 입력: "))
                break
            except ValueError:
                print("숫자로 입력해주세요.")

        # 7. CSV 저장 경로
        self.output = input("CSV 저장 경로 입력: ")

        # 8. 조합 + 저장
        filemanager = FileManager(self.lib_manager)
        combine_lines, texturefiles = filemanager.combine_file(self.selections, self.gauge)
        filemanager.save_csv(self.output, combine_lines)
        print(f"CSV 저장 완료: {self.output}")
        filemanager.copy_textures(texturefiles, os.path.dirname(self.output))
        print(f"텍스처 파일 복사 완료: {os.path.dirname(self.output)}")


if __name__ == "__main__":
    cli = PoleAssemblerCLI()
    while True:
        cli.run()
        again = input("다른 작업을 수행하시겠습니까? (y/n): ").lower()
        if again != 'y':
            print('작업을 진행하지 않습니다. 프로그램을 종료합니다.')
            input("엔터를 눌러 종료")
            break
