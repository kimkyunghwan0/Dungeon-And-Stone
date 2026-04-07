from __future__ import annotations

import random
from typing import Iterator, List, Tuple, TYPE_CHECKING

import tcod

import entity_factories
from game_map import GameMap
import tile_types

if TYPE_CHECKING:
    from engine import Engine

# 핵심 원칙: "방을 파낼 때 벽을 남기기 위해 내부만 파낸다"
# RectangularRoom = "벽 포함 박스" (x1,y1이 좌상단, x2,y2가 우하단)
class RectangularRoom:
    # 왼쪽 상단 모서리(x, y)와 너비/높이를 받아 오른쪽 하단 모서리 좌표를 계산
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    # 방의 중심 좌표를 반환 — 터널 연결 및 플레이어 배치에 사용
    def center(self) -> Tuple[int, int]:
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)

        return center_x, center_y

    @property
    # 방의 내부(바닥) 영역만 반환 — x1+1, y1+1부터 시작해 벽 한 칸을 남김
    # inner = "그 안쪽 바닥만" (벽 제외한 걸어다닐 수 있는 영역)
    def inner(self) -> Tuple[slice, slice]:
        """이 방의 내부 영역을 2D 배열 인덱스로 반환합니다"""
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    # 이 방이 다른 방(other)과 겹치는지 확인 — 겹치면 방을 배치하지 않음
    def intersects(self, other: RectangularRoom) -> bool:
        """이 방이 다른 RectangularRoom과 겹치면 True를 반환합니다."""
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )


# 방 안에 랜덤으로 몬스터(오크/트롤)를 배치하는 함수
def place_entities(
    room: RectangularRoom, dungeon: GameMap, maximum_monsters: int,
) -> None:
    # 0 ~ maximum_monsters 사이 랜덤 수만큼 몬스터 생성
    number_of_monsters = random.randint(0, maximum_monsters)

    for i in range(number_of_monsters):
        # 방 내부 임의의 좌표 선택
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        # 해당 좌표에 이미 엔티티가 없을 때만 배치
        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            if random.random() < 0.8:  # 80% 확률로 오크, 20% 확률로 트롤
                entity_factories.orc.spawn(dungeon, x, y)
            else:
                entity_factories.troll.spawn(dungeon, x, y)


# 두 점 사이를 L자 모양 복도로 연결하는 좌표를 생성하는 제너레이터
def tunnel_between(
    start: Tuple[int, int], end: Tuple[int, int]  # 시작점과 끝점의 (x, y) 좌표
) -> Iterator[Tuple[int, int]]:
    """이 두 점 사이에 L자 모양의 터널을 반환합니다."""
    x1, y1 = start
    x2, y2 = end
    if random.random() < 0.5:  # 50% 확률로 방향 결정
        # 수평 이동 후 수직 이동 (→ 그 다음 ↓)
        corner_x, corner_y = x2, y1
    else:
        # 수직 이동 후 수평 이동 (↓ 그 다음 →)
        corner_x, corner_y = x1, y2

    # Bresenham 직선 알고리즘으로 꺾이는 점까지 좌표 생성
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    # 꺾이는 점에서 끝점까지 좌표 생성
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y


# 던전 맵 전체를 생성하고 반환하는 함수
def generate_dungeon(
    max_rooms: int,             # 던전에 허용되는 최대 방의 수
    room_min_size: int,         # 방 하나의 최소 크기
    room_max_size: int,         # 방 하나의 최대 크기
    map_width: int,             # 맵 너비
    map_height: int,            # 맵 높이
    max_monsters_per_room: int, # 방당 최대 몬스터 수
    engine: Engine,             # 플레이어 엔티티 (첫 번째 방에 배치됨)
) -> GameMap:
    """던전 맵 생성"""
    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, entities=[player])

    rooms: List[RectangularRoom] = []  # 생성된 방 목록

    # 최대 방 개수만큼 반복하며 방 배치 시도
    for r in range(max_rooms):
        # 방의 너비와 높이를 최소/최대 사이에서 랜덤 결정
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        # 방이 맵 밖으로 나가지 않도록 좌표 범위 제한
        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        new_room = RectangularRoom(x, y, room_width, room_height)

        # 기존 방들과 겹치면 이 방은 건너뜀
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue

        # 방 내부를 바닥 타일로 파냄
        dungeon.tiles[new_room.inner] = tile_types.floor

        if len(rooms) == 0:
            # 첫 번째 방 — 플레이어를 방 중앙에 배치
            player.place(*new_room.center, dungeon)
        else:
            # 이후 방들 — 이전 방과 L자 복도로 연결
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor

        # 방 안에 몬스터 배치
        place_entities(new_room, dungeon, max_monsters_per_room)

        # 방을 목록에 추가
        rooms.append(new_room)

    return dungeon
