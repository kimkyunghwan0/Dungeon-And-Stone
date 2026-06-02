# 장비 아이템(무기·방어구)의 슬롯 종류와 스탯 보너스를 정의합니다.
from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent
from equipment_types import EquipmentType

if TYPE_CHECKING:
    from entity import Item


# 장착 가능한 아이템의 기본 컴포넌트 — Equipment 컴포넌트와 쌍으로 동작
class Equippable(BaseComponent):
    parent: Item

    def __init__(
        self,
        equipment_type: EquipmentType,
        power_bonus: int = 0,
        defense_bonus: int = 0,
    ):
        """장비 아이템을 초기화합니다.

        매개변수:
        - equipment_type : 장착 슬롯 종류 (WEAPON 또는 ARMOR)
        - power_bonus    : 장착 시 추가되는 공격력 보너스
        - defense_bonus  : 장착 시 추가되는 방어력 보너스
        """
        self.equipment_type = equipment_type
        self.power_bonus = power_bonus
        self.defense_bonus = defense_bonus


# 단검 — 무기 슬롯, 공격력 +2
class Dagger(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=2)


# 검 — 무기 슬롯, 공격력 +4
class Sword(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.WEAPON, power_bonus=4)


# 가죽 갑옷 — 방어구 슬롯, 방어력 +1
class LeatherArmor(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=1)


# 사슬 갑옷 — 방어구 슬롯, 방어력 +3
class ChainMail(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=3)
