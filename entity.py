from __future__ import annotations

import copy
from typing import Tuple, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from game_map import GameMap

# Entity 하위 클래스도 spawn()에서 올바른 타입을 반환받기 위한 제네릭 타입 변수
T = TypeVar("T", bound="Entity")

# 플레이어, 적, 아이템 등을 나타내는 일반적인 객체입니다.
class Entity:
    # x, y : 맵 좌표 / char : 화면에 표시될 문자 / color : 문자 색상(RGB)
    # name : 엔티티 이름 / blocks_movement : True이면 다른 엔티티가 이 위치로 이동 불가
    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        blocks_movement: bool = False,
    ):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks_movement = blocks_movement  # True이면 이 위치로 이동 불가

    def spawn(self: T, gamemap: GameMap, x: int, y: int) -> T:
        """주어진 위치에 이 인스턴스의 복사본을 생성합니다."""
        clone = copy.deepcopy(self)  # 원본 엔티티를 복사 (독립적인 새 인스턴스 생성)
        clone.x = x
        clone.y = y
        gamemap.entities.add(clone)  # 맵의 엔티티 집합에 추가
        return clone

    # 엔티티를 dx, dy만큼 이동 (현재 좌표에 더함)
    def move(self, dx: int, dy: int) -> None:
        self.x += dx
        self.y += dy