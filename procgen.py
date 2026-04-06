from __future__ import annotations

import random
from typing import Iterator, List, Tuple, TYPE_CHECKING

import tcod

from game_map import GameMap
import tile_types

if TYPE_CHECKING:
    from entity import Entity
    
# 핵심은 “방을 파낼 때 벽을 남기기 위해 내부만 파낸다”
# RectangularRoom = "벽 포함 박스"
class RectangularRoom:
    # 왼쪽 상단 모서리의 x, y 좌표를 입력받아 w와 h 매개변수(너비와 높이)를 기반으로 오른쪽 하단 모서리의 좌표를 계산
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> Tuple[int, int]:
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)

        return center_x, center_y

    @property
    # 방을 파내다. 
    # x1, y1 → 벽 위치
    # +1 → 그 안쪽부터 파기 시작
    # inner = "그 안쪽 바닥만"
    def inner(self) -> Tuple[slice, slice]:
        """이 방의 내부 영역을 2D 배열 인덱스로 반환합니다"""
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)
    
    # 주어진 방과 ( other인수에 있는) 다른 방이 겹치는지 여부를 확인
    def intersects(self, other: RectangularRoom) -> bool:
        """이 방이 다른 RectangularRoom과 겹치면 True를 반환합니다."""
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )
    
def tunnel_between(
    #  지도상의 "x"와 "y" 좌표
    start: Tuple[int, int], end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    """이 두 점 사이에 L자 모양의 터널을 반환합니다.""" 
    x1, y1 = start
    x2, y2 = end
    if random.random() < 0.5:  # 50%
        # 수평으로 이동한 다음 수직으로 이동합니다. 
        corner_x, corner_y = x2, y1
    else:
        # 수직으로 이동한 다음 수평으로 이동합니다. 
        corner_x, corner_y = x1, y2

    # 이 터널의 좌표를 생성합니다. 
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y    

# 던전 생성
def generate_dungeon(
    max_rooms: int, # 던전에 허용되는 최대 방의 수입니다
    room_min_size: int, # 방 하나의 최소 크기.
    room_max_size: int, # 방 하나의 최대 크기입니다. 
    map_width: int, # 너비
    map_height: int, # 높이
    player: Entity, # 플레이어
) -> GameMap:
    """던전 맵 생성"""
    dungeon = GameMap(map_width, map_height)

    rooms: List[RectangularRoom] = []

    # 최대 방 개수만큼 반복
    for r in range(max_rooms):
        # 방의 너비와 높이는 정해진 최소/최대값 사이중 랜덤
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        # 방의 좌표 == (던전 너비 - 방 너비 , 던전 높이 - 방 높이)
        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        # "RectangularRoom" 클래스를 사용하면 사각형을 다루기가 더 쉬워집니다. 
        new_room = RectangularRoom(x, y, room_width, room_height)

        # 다른 방들을 순회하며 이 방과 교차하는지 확인합니다. 
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue  # 이 방이 교차하므로 다음 시도로 넘어갑니다. 
        # 교차하는 방이 없으면 이 방은 유효합니다. 

        # 이 방의 내부 영역을 파냅니다. 
        dungeon.tiles[new_room.inner] = tile_types.floor

        # 첫번째 방에 플레이어 배치
        if len(rooms) == 0:
            player.x, player.y = new_room.center
        else: # 첫 번째 방 이후의 모든 방입니다. 
             # 이 방과 이전 방 사이에 터널을 파냅니다. 
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor

        # 마지막으로 새 방을 목록에 추가합니다.
        rooms.append(new_room)

    return dungeon