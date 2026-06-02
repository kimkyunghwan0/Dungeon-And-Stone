# 종족의 종류와 각 종족의 초기 스탯 보너스를 정의합니다.
from dataclasses import dataclass
from enum import auto, Enum


class RaceType(Enum):
    HUMAN = auto()
    DWARF = auto()
    BARBARIAN = auto()
    FURRY = auto()
    ELF = auto()


@dataclass
class Race:
    """종족 정보와 초기 스탯 보너스를 보유하는 데이터 클래스."""
    race_type: RaceType
    name: str           # 화면에 표시할 종족 이름
    description: str    # 종족 특성 설명 (선택 화면에 표시)
    hp_bonus: int = 0          # 시작 최대 HP 보정값
    power_bonus: int = 0       # 시작 base_power 보정값
    defense_bonus: int = 0     # 시작 base_defense 보정값
    heal_bonus: int = 0        # 회복 포션 사용 시 추가 회복량 (수인 전용)
    fov_radius: int = 8        # 시야 반경 (엘프: 10, 나머지: 8)
    level_up_base: int = 200   # 레벨업 기본 경험치 요구량 (인간: 150)


# 선택 가능한 종족 목록 — 인덱스가 선택 키(1~5)에 대응
RACES = [
    Race(
        race_type=RaceType.HUMAN,
        name="Human",
        description="Balanced. Level-up XP requirement reduced.",
        level_up_base=150,
    ),
    Race(
        race_type=RaceType.DWARF,
        name="Dwarf",
        description="HP +10, Defense +1.",
        hp_bonus=10,
        defense_bonus=1,
    ),
    Race(
        race_type=RaceType.BARBARIAN,
        name="Barbarian",
        description="Power +2, HP -5.",
        power_bonus=2,
        hp_bonus=-5,
    ),
    Race(
        race_type=RaceType.FURRY,
        name="Furry",
        description="Healing potion effect +4.",
        heal_bonus=4,
    ),
    Race(
        race_type=RaceType.ELF,
        name="Elf",
        description="Vision radius +2 (10 tiles).",
        fov_radius=10,
    ),
]
