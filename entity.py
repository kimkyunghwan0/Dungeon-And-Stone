from __future__ import annotations

import copy
from typing import Tuple, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from game_map import GameMap

T = TypeVar("T", bound="Entity")

# 플레이어, 적, 아이템 등을 나타내는 일반적인 객체입니다.
class Entity:
    # x,y : 좌표,  char : 개체 , color : entity 색상(RGB)
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
        self.blocks_movement = blocks_movement # 이동여부

    def spawn(self: T, gamemap: GameMap, x: int, y: int) -> T:
        """주어진 위치에 이 인스턴스의 복사본을 생성합니다.""" 
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        gamemap.entities.add(clone)
        return clone
    
    # move 함수 엔티티 위치 이동
    def move(self, dx: int, dy: int) -> None:
        # Move the entity by a given amount
        self.x += dx
        self.y += dy