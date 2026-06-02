# 엔티티의 장비 슬롯(무기·방어구)을 관리하고 스탯 보너스를 계산합니다.
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from components.base_component import BaseComponent
from equipment_types import EquipmentType

if TYPE_CHECKING:
    from entity import Actor, Item


# 장비 슬롯(무기·방어구)을 관리하는 컴포넌트
# Equippable 컴포넌트를 가진 아이템을 슬롯에 장착/해제하고,
# 장착된 장비의 스탯 보너스를 Fighter에 제공
class Equipment(BaseComponent):
    parent: Actor

    def __init__(self, weapon: Optional[Item] = None, armor: Optional[Item] = None):
        """장비 슬롯을 초기화합니다.

        매개변수:
        - weapon : 현재 무기 슬롯에 장착된 아이템 (없으면 None)
        - armor  : 현재 방어구 슬롯에 장착된 아이템 (없으면 None)
        """
        self.weapon = weapon
        self.armor = armor

    @property
    def defense_bonus(self) -> int:
        """장착된 장비 전체의 방어력 보너스 합계를 반환합니다.

        무기와 방어구 각각의 equippable.defense_bonus를 합산.
        Fighter.defense 프로퍼티에서 base_defense에 더해져 실제 방어력을 결정.
        """
        bonus = 0

        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.defense_bonus

        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.defense_bonus

        return bonus

    @property
    def power_bonus(self) -> int:
        """장착된 장비 전체의 공격력 보너스 합계를 반환합니다.

        무기와 방어구 각각의 equippable.power_bonus를 합산.
        Fighter.power 프로퍼티에서 base_power에 더해져 실제 공격력을 결정.
        """
        bonus = 0

        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.power_bonus

        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.power_bonus

        return bonus

    def item_is_equipped(self, item: Item) -> bool:
        """주어진 아이템이 현재 어느 슬롯에든 장착되어 있으면 True를 반환합니다.

        인벤토리 렌더링에서 장착 여부를 표시(E 표시)할 때 사용.
        아이템 버리기 전 장착 해제 여부 확인에도 사용.
        """
        return self.weapon == item or self.armor == item

    def unequip_message(self, item_name: str) -> None:
        """장비 해제 메시지를 메시지 로그에 추가합니다."""
        self.parent.gamemap.engine.message_log.add_message(
            f"{item_name}을(를) 해제했습니다."
        )

    def equip_message(self, item_name: str) -> None:
        """장비 장착 메시지를 메시지 로그에 추가합니다."""
        self.parent.gamemap.engine.message_log.add_message(
            f"{item_name}을(를) 장착했습니다."
        )

    def equip_to_slot(self, slot: str, item: Item, add_message: bool) -> None:
        """지정된 슬롯에 아이템을 장착합니다.

        동작 흐름:
        1. 해당 슬롯에 이미 장착된 아이템이 있으면 먼저 해제
        2. setattr()로 슬롯에 새 아이템을 장착
        3. add_message=True이면 장착 메시지 출력
        """
        current_item = getattr(self, slot)

        if current_item is not None:
            self.unequip_from_slot(slot, add_message)

        setattr(self, slot, item)

        if add_message:
            self.equip_message(item.name)

    def unequip_from_slot(self, slot: str, add_message: bool) -> None:
        """지정된 슬롯의 아이템을 해제합니다.

        동작 흐름:
        1. add_message=True이면 해제 메시지 출력
        2. setattr()로 슬롯을 None으로 비움
        """
        current_item = getattr(self, slot)

        if add_message:
            self.unequip_message(current_item.name)

        setattr(self, slot, None)

    def toggle_equip(self, equippable_item: Item, add_message: bool = True) -> None:
        """아이템의 장착/해제를 전환합니다.

        동작 흐름:
        1. 아이템의 equipment_type이 WEAPON이면 "weapon" 슬롯, 아니면 "armor" 슬롯을 선택
        2. 해당 슬롯에 이미 같은 아이템이 있으면 해제(unequip_from_slot)
        3. 없으면 장착(equip_to_slot)

        인벤토리에서 'i' 키로 아이템을 선택했을 때 EquipAction이 이 메서드를 호출.
        """
        if (
            equippable_item.equippable
            and equippable_item.equippable.equipment_type == EquipmentType.WEAPON
        ):
            slot = "weapon"
        else:
            slot = "armor"

        if getattr(self, slot) == equippable_item:
            self.unequip_from_slot(slot, add_message)
        else:
            self.equip_to_slot(slot, equippable_item, add_message)
