from __future__ import annotations

from typing import List, TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor, Item


# 엔티티의 아이템 목록을 관리하는 컴포넌트
class Inventory(BaseComponent):
    parent: Actor

    def __init__(self, capacity: int):
        """인벤토리를 초기화합니다.

        매개변수:
        - capacity : 최대 보유 가능 아이템 수
                     플레이어는 26(a~z), 몬스터는 0으로 설정됨.
        - items    : 현재 보유 중인 아이템 목록 (빈 리스트로 시작)
        """
        self.capacity = capacity
        self.items: List[Item] = []

    def drop(self, item: Item) -> None:
        """인벤토리에서 아이템을 제거하고 현재 위치 맵에 내려놓습니다.

        동작 흐름:
        1. items 목록에서 해당 아이템을 제거 (인벤토리 소속 해제)
        2. item.place()로 소유자(parent)의 현재 맵 좌표에 아이템을 배치
           - 아이템의 parent가 다시 GameMap으로 변경되어 맵 엔티티로 등록됨
           - 버린 자리에 가면 다시 주울 수 있음
        3. 버리기 메시지를 메시지 로그에 출력
        """
        self.items.remove(item)
        item.place(self.parent.x, self.parent.y, self.gamemap)

        # self.engine.message_log.add_message(f"{item.name}을(를) 버렸다.")
        self.engine.message_log.add_message(f"You dropped the {item.name}.")
