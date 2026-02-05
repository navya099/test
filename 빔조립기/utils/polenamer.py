from Electric.Overhead.Pole.poletype import PoleType
from utils.funtion import format_meter


class PoleNameBuilder:
    @staticmethod
    def build(pole) -> str:
        t = pole.type
        length = format_meter(pole.length) #str
        if t == PoleType.PIPE:
            return f"{t.value}-{pole.width}-{length}m"

        if t == PoleType.STEEL:
            return (
                f"{t.value}-"
                f"{install.leg_size}-"
                f"{install.web_spacing}-"
                f"{int(install.pole_height)}m"
            )

        if t == PoleType.H_BEAM:
            return (
                f"{t.value}-"
                f"{install.section_size}-"
                f"{int(install.pole_height)}m"
            )

        raise ValueError(f"지원하지 않는 전주 타입: {t}")
