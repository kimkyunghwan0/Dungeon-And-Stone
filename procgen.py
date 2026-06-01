# 절차적 던전 생성(방 배치, 복도 연결, 몬스터·아이템 배치)을 담당합니다.
from __future__ import annotations

import random
from typing import Dict, Iterator, List, Tuple, TYPE_CHECKING

import tcod

import entity_factories
from game_map import GameMap
import tile_types

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity

# 층별 최대 아이템 수: (최소 층, 최대 아이템 수) — 해당 층 이상부터 적용
max_items_by_floor = [
    (1, 1),  # 1층부터: 방당 최대 1개
    (4, 2),  # 4층부터: 방당 최대 2개
]

# 층별 최대 몬스터 수: (최소 층, 최대 몬스터 수)
max_monsters_by_floor = [
    (1, 2),  # 1층부터: 방당 최대 2마리
    (4, 3),  # 4층부터: 방당 최대 3마리
    (6, 5),  # 6층부터: 방당 최대 5마리
]

# 층별 아이템 등장 가중치: {최소 층: [(아이템, 가중치), ...]}
# 해당 층 이상부터 그 아이템이 등장 후보에 추가됨
item_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.health_potion, 35)],       # 모든 층: 회복 포션
    2: [(entity_factories.confusion_scroll, 10)],    # 2층부터: 혼란 스크롤 추가
    4: [(entity_factories.lightning_scroll, 25), (entity_factories.sword, 5)],    # 4층부터: 번개 스크롤, 칼 추가
    6: [(entity_factories.fireball_scroll, 25), (entity_factories.chain_mail, 15)],     # 6층부터: 파이어볼 스크롤, 방어구 추가
}

# 층별 몬스터 등장 가중치: {최소 층: [(몬스터, 가중치), ...]}
# 층이 깊어질수록 트롤 비중이 높아짐
enemy_chances: Dict[int, List[Tuple[Entity, int]]] = {
    0: [(entity_factories.orc, 80)],    # 모든 층: 오크
    3: [(entity_factories.troll, 15)],  # 3층부터: 트롤 15%
    5: [(entity_factories.troll, 30)],  # 5층부터: 트롤 30%
    7: [(entity_factories.troll, 60)],  # 7층부터: 트롤 60%
}

def get_max_value_for_floor(
    max_value_by_floor: List[Tuple[int, int]], floor: int
) -> int:
    """현재 층에 해당하는 최댓값을 반환합니다.

    동작 흐름:
    - max_value_by_floor를 순서대로 순회하며 floor_minimum ≤ floor인 값을 current_value에 갱신
    - floor_minimum > floor 이면 중단 (이후 항목은 아직 해당 층 미달)
    - 예) floor=3, [(1,2),(4,3),(6,5)] → floor_minimum 4 > 3에서 중단, 2 반환

    place_entities()에서 max_monsters_by_floor / max_items_by_floor에 대해 호출됨.
    """
    current_value = 0

    for floor_minimum, value in max_value_by_floor:
        if floor_minimum > floor:
            break
        else:
            current_value = value

    return current_value

def get_entities_at_random(
    weighted_chances_by_floor: Dict[int, List[Tuple[Entity, int]]],
    number_of_entities: int,
    floor: int,
) -> List[Entity]:
    """현재 층에 맞는 엔티티를 가중치 기반으로 무작위 선택해 반환합니다.

    동작 흐름:
    1. weighted_chances_by_floor를 순회해 key(최소 층) ≤ floor인 항목만 수집
       → 현재 층에서 등장 가능한 후보와 가중치를 entity_weighted_chances에 저장
       (층이 높아질수록 더 강한 몬스터·유용한 아이템이 후보에 추가됨)
    2. random.choices()로 가중치 비례 무작위 추출 (k=number_of_entities)
    3. 선택된 엔티티 리스트 반환

    place_entities()에서 enemy_chances / item_chances에 대해 호출됨.
    """
    entity_weighted_chances = {}

    for key, values in weighted_chances_by_floor.items():
        if key > floor:
            break
        else:
            for value in values:
                entity = value[0]
                weighted_chance = value[1]

                entity_weighted_chances[entity] = weighted_chance

    entities = list(entity_weighted_chances.keys())
    entity_weighted_chance_values = list(entity_weighted_chances.values())

    chosen_entities = random.choices(
        entities, weights=entity_weighted_chance_values, k=number_of_entities
    )

    return chosen_entities

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


def place_entities(room: RectangularRoom, dungeon: GameMap, floor_number: int,) -> None:
    """방 안에 현재 층 기준으로 몬스터와 아이템을 무작위 배치합니다.

    동작 흐름:
    1. get_max_value_for_floor()로 현재 층에 맞는 최대 몬스터·아이템 수 결정
    2. get_entities_at_random()으로 enemy_chances/item_chances 가중치 테이블에서
       등장할 엔티티를 무작위 선택 (층이 높을수록 강한 적·다양한 아이템이 후보에 포함)
    3. 방 내부 임의 좌표에 배치 (이미 엔티티가 있는 칸은 건너뜀)
    """
    number_of_monsters = random.randint(
        0, get_max_value_for_floor(max_monsters_by_floor, floor_number)
    )
    number_of_items = random.randint(
        0, get_max_value_for_floor(max_items_by_floor, floor_number)
    )

    monsters: List[Entity] = get_entities_at_random(
        enemy_chances, number_of_monsters, floor_number
    )
    items: List[Entity] = get_entities_at_random(
        item_chances, number_of_items, floor_number
    )

    for entity in monsters + items:
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
           entity.spawn(dungeon, x, y)


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
    engine: Engine,
) -> GameMap:
    """던전 맵 전체를 생성하고 반환합니다.

    매개변수:
    - max_rooms            : 던전에 허용되는 최대 방의 수
    - room_min_size        : 방 하나의 최소 크기
    - room_max_size        : 방 하나의 최대 크기
    - map_width, map_height: 맵 크기
    - engine               : 게임 엔진 (플레이어 엔티티·현재 층 정보 접근에 사용)

    동작 흐름:
    1. GameMap 생성 (전체가 벽으로 초기화된 상태, 플레이어만 포함)
    2. max_rooms번 반복하며 방 배치 시도:
       a. 너비/높이를 min~max 사이 랜덤으로 결정
       b. 맵 밖으로 나가지 않도록 좌표 범위 제한
       c. 기존 방들과 겹치면(intersects) 이 방을 건너뜀
       d. 겹치지 않으면 inner 영역을 바닥 타일로 파냄
       e. 첫 번째 방: 플레이어를 방 중심에 배치
          이후 방들: 이전 방과 L자 복도(tunnel_between)로 연결
       f. place_entities()로 현재 층 기준 몬스터·아이템 배치
    3. 완성된 GameMap 반환
    """
    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, entities=[player])

    rooms: List[RectangularRoom] = []  # 생성된 방 목록

    center_of_last_room = (0, 0)

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
            center_of_last_room = new_room.center

        # 방 안에 몬스터, 아이템 배치
        place_entities(new_room, dungeon, engine.game_world.current_floor)

        dungeon.tiles[center_of_last_room] = tile_types.down_stairs
        dungeon.downstairs_location = center_of_last_room

        # 생성된 방 목록에 추가
        rooms.append(new_room)

    return dungeon
