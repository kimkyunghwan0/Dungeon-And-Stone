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
    def __init__(self, x: int, y: int, width: int, height: int):
        """직사각형 방을 초기화합니다.

        매개변수:
        - x, y         : 방의 좌상단 모서리 좌표 (벽 포함)
        - width, height: 방의 너비와 높이 (벽 포함)

        x1, y1 = 좌상단 (벽 포함 시작)
        x2, y2 = 우하단 (벽 포함 끝)
        실제 걸어다닐 수 있는 바닥은 inner 프로퍼티로 접근 (벽 한 칸씩 안쪽).
        """
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> Tuple[int, int]:
        """방의 중심 좌표를 반환합니다.

        동작 흐름:
        - (x1+x2)/2, (y1+y2)/2 를 정수로 계산
        - 첫 번째 방: 플레이어 시작 위치로 사용
        - 이후 방들: 이전 방과 이 방을 L자 복도로 연결하는 시작/끝 좌표로 사용
        """
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)
        return center_x, center_y

    @property
    def inner(self) -> Tuple[slice, slice]:
        """방의 내부(바닥) 영역을 numpy 슬라이스로 반환합니다.

        동작 흐름:
        - x1+1부터 x2, y1+1부터 y2 까지 → 사방 한 칸씩 벽을 남김
        - dungeon.tiles[new_room.inner] = tile_types.floor 처럼 numpy 인덱싱으로 바닥을 파낼 때 사용
        - inner 영역은 실제로 걸어다닐 수 있는 바닥 타일이 될 범위
        """
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    def intersects(self, other: RectangularRoom) -> bool:
        """이 방이 다른 방과 겹치면 True를 반환합니다.

        동작 흐름:
        - AABB(축 정렬 경계 박스) 겹침 검사
        - 두 박스가 x축과 y축 모두에서 겹칠 때만 True
        - generate_dungeon()에서 새 방이 기존 방들과 겹치는지 확인할 때 사용
          → 겹치면 그 방을 건너뜀 (방이 서로 붙어있거나 내부가 합쳐지지 않도록)
        """
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )


def place_entities(
    room: RectangularRoom, dungeon: GameMap, maximum_monsters: int, maximum_items: int
) -> None:
    """방 안에 랜덤으로 몬스터와 아이템을 배치합니다.

    동작 흐름 (몬스터):
    1. 0 ~ maximum_monsters 사이 랜덤 수만큼 몬스터 생성 시도
    2. 방 내부(x1+1 ~ x2-1, y1+1 ~ y2-1) 임의 좌표 선택
    3. 해당 좌표에 이미 엔티티가 없을 때만 배치
    4. 80% 확률로 오크(약함), 20% 확률로 트롤(강함) 소환

    동작 흐름 (아이템):
    1. 0 ~ maximum_items 사이 랜덤 수만큼 아이템 생성 시도
    2. 방 내부 임의 좌표 선택 (몬스터와 같은 방식)
    3. 해당 좌표에 이미 엔티티가 없을 때만 배치
    4. random.random()으로 아이템 종류 결정:
       - < 0.7 (70%) : 회복 포션
       - < 0.8 (10%) : 파이어볼 스크롤
       - < 0.9 (10%) : 혼란 스크롤
       - 나머지 (10%): 번개 스크롤
    """
    number_of_monsters = random.randint(0, maximum_monsters)
    number_of_items = random.randint(0, maximum_items)

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

    for i in range(number_of_items):
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            item_chance = random.random()

            if item_chance < 0.7:
                entity_factories.health_potion.spawn(dungeon, x, y)
            elif item_chance < 0.8:
                entity_factories.fireball_scroll.spawn(dungeon, x, y)
            elif item_chance < 0.9:
                entity_factories.confusion_scroll.spawn(dungeon, x, y)
            else:
                entity_factories.lightning_scroll.spawn(dungeon, x, y)


def tunnel_between(
    start: Tuple[int, int], end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    """두 점 사이를 L자 모양의 복도로 연결하는 좌표를 생성합니다.

    동작 흐름:
    1. 50% 확률로 꺾이는 방향을 결정
       - 수평 먼저(→↓): corner = (x2, y1) → x축 이동 후 y축 이동
       - 수직 먼저(↓→): corner = (x1, y2) → y축 이동 후 x축 이동
    2. tcod.los.bresenham()으로 시작점 → 꺾이는 점까지 직선 좌표 생성
    3. 꺾이는 점 → 끝점까지 직선 좌표 생성
    4. 두 구간의 좌표를 순서대로 yield

    결과적으로 두 방의 중심을 L자 형태의 복도로 이어줌.
    generate_dungeon()에서 이 좌표들을 바닥 타일로 파내 실제 복도를 만듦.
    """
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


def generate_dungeon(
    max_rooms: int,
    room_min_size: int,
    room_max_size: int,
    map_width: int,
    map_height: int,
    max_monsters_per_room: int,
    max_items_per_room: int,
    engine: Engine,
) -> GameMap:
    """던전 맵 전체를 생성하고 반환합니다.

    매개변수:
    - max_rooms            : 던전에 허용되는 최대 방의 수
    - room_min_size        : 방 하나의 최소 크기
    - room_max_size        : 방 하나의 최대 크기
    - map_width, map_height: 맵 크기
    - max_monsters_per_room: 방당 최대 몬스터 수
    - max_items_per_room   : 방당 최대 아이템 수
    - engine               : 게임 엔진 (플레이어 엔티티 접근에 사용)

    동작 흐름:
    1. GameMap 생성 (전체가 벽으로 초기화된 상태, 플레이어만 포함)
    2. max_rooms번 반복하며 방 배치 시도:
       a. 너비/높이를 min~max 사이 랜덤으로 결정
       b. 맵 밖으로 나가지 않도록 좌표 범위 제한
       c. 기존 방들과 겹치면(intersects) 이 방을 건너뜀
       d. 겹치지 않으면 inner 영역을 바닥 타일로 파냄
       e. 첫 번째 방: 플레이어를 방 중심에 배치
          이후 방들: 이전 방과 L자 복도(tunnel_between)로 연결
       f. 방 안에 몬스터와 아이템 배치 (place_entities)
    3. 완성된 GameMap 반환
    """
    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, entities=[player])

    rooms: List[RectangularRoom] = []  # 생성된 방 목록

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

        # 방 안에 몬스터, 아이템 배치
        place_entities(new_room, dungeon, max_monsters_per_room, max_items_per_room)

        rooms.append(new_room)

    return dungeon
