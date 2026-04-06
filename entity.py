from typing import Tuple


class Entity:
    
    # 플레이어, 적, 아이템 등을 나타내는 일반적인 객체입니다.
    # x,y : 좌표,  char : 개체 , color : entity 색상(RGB)
    def __init__(self, x: int, y: int, char: str, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.char = char
        self.color = color

    # move 함수 엔티티 위치 이동
    def move(self, dx: int, dy: int) -> None:
        # Move the entity by a given amount
        self.x += dx
        self.y += dy