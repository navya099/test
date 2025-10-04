import os


class LibraryManager:
    """
    철도표준라이브러리 관리 클래스(전차선분야)
    Attributes:
        base_dir: 라이브러리 경로
        base: 기본 공통 라이브러리
        highspeedrail: 고속철도
        normalspeedrail: 일반철도
        subhighspeedrail: 준고속철도
    """
    def __init__(self, base_dir: str = r"D:\BVE\루트\Railway\Object\철도표준라이브러리\전철전력"):
        self.base_dir = base_dir
        self.base = {}
        self.highspeedrail = {}
        self.normalspeedrail = {}
        self.subhighspeedrail = {}
        self.textures = {}

    def scan_library(self):
        """기본 디렉토리에서 라이브러리 구조를 탐색해서 딕셔너리로 저장"""
        if not os.path.exists(self.base_dir):
            raise FileNotFoundError(f"라이브러리 폴더가 존재하지 않습니다: {self.base_dir}")

        for category in os.listdir(self.base_dir):
            category_path = os.path.join(self.base_dir, category)
            if not os.path.isdir(category_path):
                continue

            # 부품(전주, 브래킷 등)별 파일 목록 저장
            part_dict = {}
            for part in os.listdir(category_path):
                part_path = os.path.join(category_path, part)
                if os.path.isdir(part_path):
                    part_dict[part] = [
                        f for f in os.listdir(part_path)
                        if f.lower().endswith(".csv")
                    ]

                    # PNG는 textures 딕셔너리에 저장 (전체 경로)
                    for f in os.listdir(part_path):
                        if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                            self.textures[f] = os.path.join(part_path, f)

            if "공통" in category or "기본" in category:
                self.base = part_dict
            elif "고속철도" in category:
                self.highspeedrail = part_dict
            elif "일반철도" in category:
                self.normalspeedrail = part_dict
            elif "cako250" in category:
                self.subhighspeedrail = part_dict

    def list_categories_grouped(self) -> dict[str, list[str]]:
        """라이브러리별 카테고리 목록 반환"""
        return {
            "base": list(self.base.keys()),
            "highspeedrail": list(self.highspeedrail.keys()),
            "normalspeedrail": list(self.normalspeedrail.keys()),
            "subhighspeedrail": list(self.subhighspeedrail.keys())
        }

    def list_files_in_category(self, category: str, group: str = None) -> list[str]:
        """
        특정 카테고리 내 파일명 조회
        group: 'base', 'highspeedrail', 'normalspeedrail', 'subhighspeedrail'
        """
        libs = {
            "base": self.base,
            "highspeedrail": self.highspeedrail,
            "normalspeedrail": self.normalspeedrail,
            "subhighspeedrail": self.subhighspeedrail
        }

        if group:
            return libs.get(group, {}).get(category, [])

        # group이 없으면 4개 라이브러리 모두 검색
        for lib in libs.values():
            if category in lib:
                return lib[category]
        return []

    def search_file(self, keyword: str, group: str = None) -> dict[str, list[str]]:
        """
        파일명에서 키워드 검색
        Args:
            keyword: 검색어
            group: 'base', 'highspeedrail', 'normalspeedrail', 'subhighspeedrail' 선택 가능, None이면 전체
        Returns:
            {카테고리: [파일1, 파일2, ...]}
        """
        libs = {
            "base": self.base,
            "highspeedrail": self.highspeedrail,
            "normalspeedrail": self.normalspeedrail,
            "subhighspeedrail": self.subhighspeedrail
        }

        search_libs = {group: libs[group]} if group else libs

        result = {}
        for lib_name, lib in search_libs.items():
            for category, files in lib.items():
                matched = [f for f in files if keyword.lower() in f.lower()]
                if matched:
                    result[f"{lib_name}:{category}"] = matched
        return result

    def list_all_files(self, group: str = None) -> list[str]:
        """전체 라이브러리 혹은 특정 그룹의 모든 파일 반환"""
        libs = {"base": self.base,
                "highspeedrail": self.highspeedrail,
                "normalspeedrail": self.normalspeedrail,
                "subhighspeedrail": self.subhighspeedrail}
        search_libs = {group: libs[group]} if group else libs
        all_files = []
        for lib in search_libs.values():
            for files in lib.values():
                all_files.extend(files)
        return all_files
