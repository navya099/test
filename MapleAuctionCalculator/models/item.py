# models/item.py

from models.option import StatOption


class Item:
    """
    장비 하나의 정보를 저장하는 모델.

    구조:

        Item
        ├── 기본 정보
        ├── 가격 정보
        ├── 스타포스
        ├── 추옵
        ├── 작
        ├── 잠재
        └── 에디셔널 잠재
    """

    def __init__(
            self,
            name="",
            slot="",
            starforce=0,

            # 가격
            price=0.0,
            tax=False,
            used_count=0,
            max_count=10,

            # 새로운 옵션 구조
            flame_options=None,
            scroll_options=None,
            potential_grade="",
            potential_options=None,
            additional_grade="",
            additional_potential_options=None,

            # ========================================================
            # 기존 코드 호환용
            # ========================================================
            flame_int=0.0,
            flame_all=0.0,

            scroll_int=0.0,
            scroll_magic=0.0,

            potential_int=0.0,

            additional_int=0.0,
            additional_magic=0.0,
    ):

        # ========================================================
        # 기본 정보
        # ========================================================

        self.name = name
        self.slot = slot
        self.starforce = int(starforce)

        # ========================================================
        # 가격 정보
        # ========================================================

        self.price = float(price)
        self.tax = bool(tax)

        self.used_count = int(used_count)
        self.max_count = int(max_count)

        # ========================================================
        # 추옵
        # ========================================================

        self.flame_options = (
            list(flame_options)
            if flame_options is not None
            else []
        )

        # 기존 방식으로 전달된 옵션을 새 구조로 변환
        if flame_int:
            self.flame_options.append(
                StatOption("INT", flame_int)
            )

        if flame_all:
            self.flame_options.append(
                StatOption("올스탯%", flame_all)
            )

        # ========================================================
        # 작
        # ========================================================

        self.scroll_options = (
            list(scroll_options)
            if scroll_options is not None
            else []
        )

        # 기존 방식 호환
        if scroll_int:
            self.scroll_options.append(
                StatOption("INT", scroll_int)
            )

        if scroll_magic:
            self.scroll_options.append(
                StatOption("마력", scroll_magic)
            )

        # ========================================================
        # 잠재
        # ========================================================

        self.potential_grade = potential_grade

        self.potential_options = (
            list(potential_options)
            if potential_options is not None
            else []
        )

        # 기존 방식 호환
        if potential_int:
            self.potential_options.append(
                StatOption("INT%", potential_int)
            )

        # ========================================================
        # 에디셔널 잠재
        # ========================================================

        self.additional_grade = additional_grade

        self.additional_potential_options = (
            list(additional_potential_options)
            if additional_potential_options is not None
            else []
        )

        # 기존 방식 호환
        if additional_int:
            self.additional_potential_options.append(
                StatOption("INT%", additional_int)
            )

        if additional_magic:
            self.additional_potential_options.append(
                StatOption("마력", additional_magic)
            )

    # ========================================================
    # 계산용 속성
    # ========================================================

    @property
    def remaining_count(self):
        return self.max_count - self.used_count

    @property
    def actual_price(self):
        """
        관세가 체크되어 있으면 10% 추가.
        """

        if self.tax:
            return self.price * 1.10

        return self.price

    # ========================================================
    # 옵션 추가
    # ========================================================

    def add_flame_option(self, stat, value):
        self.flame_options.append(
            StatOption(stat, value)
        )

    def add_scroll_option(self, stat, value):
        self.scroll_options.append(
            StatOption(stat, value)
        )

    def add_potential_option(self, stat, value):
        self.potential_options.append(
            StatOption(stat, value)
        )

    def add_additional_potential_option(
        self,
        stat,
        value
    ):
        self.additional_potential_options.append(
            StatOption(stat, value)
        )

    # ========================================================
    # 기존 코드 호환용
    #
    # 현재 calculator.py가 아직
    #
    # item.flame_int
    # item.flame_all
    # item.scroll_int
    #
    # 등을 사용하고 있기 때문에 당장은 유지한다.
    # ========================================================

    @property
    def flame_int(self):
        return self._get_option_value(
            self.flame_options,
            "INT"
        )

    @property
    def flame_all(self):
        return self._get_option_value(
            self.flame_options,
            "올스탯%"
        )

    @property
    def scroll_int(self):
        return self._get_option_value(
            self.scroll_options,
            "INT"
        )

    @property
    def scroll_magic(self):
        return self._get_option_value(
            self.scroll_options,
            "마력"
        )

    @property
    def potential_int(self):
        return self._get_option_value(
            self.potential_options,
            "INT%"
        )

    @property
    def additional_int(self):
        return self._get_option_value(
            self.additional_potential_options,
            "INT%"
        )

    @property
    def additional_magic(self):
        return self._get_option_value(
            self.additional_potential_options,
            "마력"
        )

    @staticmethod
    def _get_option_value(options, stat):
        """
        특정 옵션의 값을 가져온다.

        같은 스탯이 여러 줄 존재하는 경우
        전부 합산한다.

        예:
            INT +12%
            INT +9%
            INT +9%

        → 30
        """

        total = 0.0

        for option in options:

            if option.stat == stat:
                total += option.value

        return total

    # ========================================================
    # 표시용
    # ========================================================

    @staticmethod
    def _options_text(options):

        if not options:
            return "-"

        return " / ".join(
            option.text()
            for option in options
        )

    # --------------------------------------------------------
    # 추옵
    # --------------------------------------------------------

    def flame_text(self):
        return self._options_text(
            self.flame_options
        )

    # --------------------------------------------------------
    # 작
    # --------------------------------------------------------

    def scroll_text(self):
        return self._options_text(
            self.scroll_options
        )

    # --------------------------------------------------------
    # 잠재
    # --------------------------------------------------------

    def potential_text(self):

        if not self.potential_options:
            return "-"

        text = self._options_text(
            self.potential_options
        )

        if self.potential_grade:
            return f"[{self.potential_grade}] {text}"

        return text

    # --------------------------------------------------------
    # 에디셔널 잠재
    # --------------------------------------------------------

    def additional_text(self):

        if not self.additional_potential_options:
            return "-"

        text = self._options_text(
            self.additional_potential_options
        )

        if self.additional_grade:
            return f"[{self.additional_grade}] {text}"

        return text

    # ========================================================
    # JSON 저장
    # ========================================================

    def to_dict(self):

        return {

            # ------------------------------------------------
            # 기본 정보
            # ------------------------------------------------

            "name": self.name,
            "slot": self.slot,
            "starforce": self.starforce,

            # ------------------------------------------------
            # 가격
            # ------------------------------------------------

            "price": self.price,
            "tax": self.tax,
            "used_count": self.used_count,
            "max_count": self.max_count,

            # ------------------------------------------------
            # 추옵
            # ------------------------------------------------

            "flame_options": [
                option.to_dict()
                for option in self.flame_options
            ],

            # ------------------------------------------------
            # 작
            # ------------------------------------------------

            "scroll_options": [
                option.to_dict()
                for option in self.scroll_options
            ],

            # ------------------------------------------------
            # 잠재
            # ------------------------------------------------

            "potential_grade": self.potential_grade,

            "potential_options": [
                option.to_dict()
                for option in self.potential_options
            ],

            # ------------------------------------------------
            # 에디셔널
            # ------------------------------------------------

            "additional_grade": self.additional_grade,

            "additional_potential_options": [
                option.to_dict()
                for option in self.additional_potential_options
            ],
        }

    # ========================================================
    # JSON 불러오기
    # ========================================================

    @classmethod
    def from_dict(cls, data):

        # ----------------------------------------------------
        # 새로운 형식
        # ----------------------------------------------------

        if "flame_options" in data:

            flame_options = [
                StatOption.from_dict(option)
                for option in data.get(
                    "flame_options",
                    []
                )
            ]

            scroll_options = [
                StatOption.from_dict(option)
                for option in data.get(
                    "scroll_options",
                    []
                )
            ]

            potential_options = [
                StatOption.from_dict(option)
                for option in data.get(
                    "potential_options",
                    []
                )
            ]

            additional_options = [
                StatOption.from_dict(option)
                for option in data.get(
                    "additional_potential_options",
                    []
                )
            ]

            return cls(
                name=data.get("name", ""),

                slot=data.get(
                    "slot",
                    ""
                ),

                starforce=data.get(
                    "starforce",
                    0
                ),

                price=data.get(
                    "price",
                    0
                ),

                tax=data.get(
                    "tax",
                    False
                ),

                used_count=data.get(
                    "used_count",
                    0
                ),

                max_count=data.get(
                    "max_count",
                    10
                ),

                flame_options=flame_options,

                scroll_options=scroll_options,

                potential_grade=data.get(
                    "potential_grade",
                    ""
                ),

                potential_options=potential_options,

                additional_grade=data.get(
                    "additional_grade",
                    ""
                ),

                additional_potential_options=(
                    additional_options
                ),
            )

        # ----------------------------------------------------
        # 기존 v2 / v3 형식
        #
        # 기존 JSON도 읽을 수 있도록 한다.
        # ----------------------------------------------------

        item = cls(
            name=data.get(
                "name",
                ""
            ),

            price=data.get(
                "price",
                0
            ),

            used_count=data.get(
                "used_count",
                0
            ),

            max_count=data.get(
                "max_count",
                10
            ),

            tax=data.get(
                "tax",
                False
            ),
        )

        # ----------------------------------------------------
        # 기존 추옵
        # ----------------------------------------------------

        if data.get("flame_int", 0):
            item.add_flame_option(
                "INT",
                data["flame_int"]
            )

        if data.get("flame_all", 0):
            item.add_flame_option(
                "올스탯%",
                data["flame_all"]
            )

        # ----------------------------------------------------
        # 기존 작
        # ----------------------------------------------------

        if data.get("scroll_int", 0):
            item.add_scroll_option(
                "INT",
                data["scroll_int"]
            )

        if data.get("scroll_magic", 0):
            item.add_scroll_option(
                "마력",
                data["scroll_magic"]
            )

        # ----------------------------------------------------
        # 기존 잠재
        # ----------------------------------------------------

        if data.get("potential_int", 0):

            item.potential_grade = ""

            item.add_potential_option(
                "INT%",
                data["potential_int"]
            )

        # ----------------------------------------------------
        # 기존 에디
        # ----------------------------------------------------

        if data.get("additional_int", 0):

            item.add_additional_potential_option(
                "INT%",
                data["additional_int"]
            )

        if data.get("additional_magic", 0):

            item.add_additional_potential_option(
                "마력",
                data["additional_magic"]
            )

        return item