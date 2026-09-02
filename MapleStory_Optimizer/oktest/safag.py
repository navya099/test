from mapledataclass.add_ability import AddAbility  # 오타 수정된 경로
from mapledataclass.base_stats import BaseStats
from mapledataclass.equipment import Equipment
from mapledataclass.scroll import Scroll
from mapledataclass.starforce import Starforce

# 1. 아케인셰이드 무기 객체 생성
arcane_weapon = Equipment(
    name="아케인셰이드 환검",
    # base_stats 내부에 boss_atk 스탯이 선언되어 있다고 가정합니다.
    base_stats=BaseStats(
        str_val=100,
        dex_val=100,
        atk=295,
        ignore_def=20,
    ),
    starforce_info=Starforce(  # 필드명 매핑 수정
        star=18,
        req_level=200
    ),
    add_ability=AddAbility(   # 오타 및 필드명 수정
        stats=BaseStats(
            str_val=55,
            int_val=30,
            luk_val=30,
            dmg=4,
            atk=142,
        )
    ),
    scroll=Scroll(stats=BaseStats(
        atk=81,
        str_val=36,
    ))
)

# ==================================================
# 🧪 2. 기능 검증을 위한 테스트 출력부 (파이참 콘솔)
# ==================================================
print(f"==================================================")
print(f"       ⚔️ 생성된 장비 검증 테스트 완료")
print(f"==================================================")
print(f"📦 장비 이름 : {arcane_weapon.name}")
print(f"★ 스타포스   : {arcane_weapon.starforce_info.star}성 (렙제: {arcane_weapon.starforce_info.req_level}제)")
print(f"--------------------------------------------------")

# 앞서 구현한 get_final_flat_stats() 함수를 호출하여 합산 연산 검증
final_stats = arcane_weapon.get_final_flat_stats()

print(f"🔥 [최종 합산 깡스탯 결과]")
print(f"🔹 총 STR     : {final_stats.str_val} (기본 {arcane_weapon.base_stats.str_val} + 추옵{arcane_weapon.add_ability.stats.str_val} + 스타포스{arcane_weapon.starforce_info.get_bonus_stats().str_val} + 주문서{arcane_weapon.scroll.stats.str_val})")
print(f"💥 총 공격력  : {final_stats.atk} (기본 {arcane_weapon.base_stats.atk} + 추옵{arcane_weapon.add_ability.stats.atk} + 스타포스{arcane_weapon.starforce_info.get_bonus_stats().atk} + 주문서{arcane_weapon.scroll.stats.atk})")
print(f"🔰 총 방무  : {arcane_weapon.base_stats.ignore_def}%")
print(f"==================================================")
