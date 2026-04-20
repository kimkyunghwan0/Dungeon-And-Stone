from __future__ import annotations

from typing import Iterable, Iterator, Optional, TYPE_CHECKING

import numpy as np  # type: ignore
from tcod.console import Console

from entity import Actor, Item
import tile_types

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity


# 맵 전체 정보(타일, 엔티티, 시야)를 관리하는 클래스
class GameMap:
    def __init__(
        self, engine: Engine, width: int, height: int, entities: Iterable[Entity] = ()
    ):
        """GameMap을 초기화합니다.

        매개변수:
        - engine   : 게임 엔진 참조 (컴포넌트에서 engine에 접근하기 위해 저장)
        - width, height : 맵 크기 (타일 단위)
        - entities : 초기 배치할 엔티티 목록 (보통 플레이어만 포함해서 생성)

        tiles  : 맵 전체 타일 배열 (초기값 = 전부 벽)
                 numpy structured array로 "walkable", "transparent", "light", "dark" 필드를 가짐
        visible  : 현재 시야에 보이는 타일 여부 (매 턴 update_fov()로 갱신)
        explored : 한 번이라도 본 타일 여부 (한 번 True가 되면 False로 돌아가지 않음)
        """
        self.engine = engine
        self.width, self.height = width, height
        self.entities = set(entities)  # 중복 없는 엔티티 집합

        # np.full(크기, 채울값) — 맵 전체를 기본값(벽)으로 초기화
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order="F")

        # visible  : 플레이어가 현재 볼 수 있는 타일 (매 턴 update_fov()로 갱신)
        self.visible = np.full((width, height), fill_value=False, order="F")
        # explored : 한 번이라도 본 타일 (어둡게라도 계속 표시됨)
        self.explored = np.full((width, height), fill_value=False, order="F")

    @property
    def gamemap(self) -> GameMap:
        """자기 자신을 반환합니다.

        Entity.gamemap이 'parent.gamemap'을 호출하는데,
        parent가 GameMap일 때 이 프로퍼티가 호출되어 자기 자신을 반환함.
        (parent가 Inventory일 때는 Inventory.gamemap이 호출됨)
        """
        return self

    @property
    def actors(self) -> Iterator[Actor]:
        """맵에 있는 살아있는 Actor(플레이어 + 몬스터)를 순회합니다.

        동작 흐름:
        - 전체 entities에서 Actor 인스턴스이고 is_alive(ai가 None이 아닌)인 것만 필터링
        - 시체(ai=None인 Actor)는 포함되지 않음
        - handle_enemy_turns()나 파이어볼 범위 판정 등에서 살아있는 캐릭터만 처리할 때 사용
        """
        yield from (
            entity
            for entity in self.entities
            if isinstance(entity, Actor) and entity.is_alive
        )

    @property
    def items(self) -> Iterator[Item]:
        """맵에 놓인 아이템 엔티티를 순회합니다.

        동작 흐름:
        - 전체 entities에서 Item 인스턴스만 필터링해 반환
        - PickupAction에서 플레이어 발 아래 아이템을 찾을 때 사용
        """
        yield from (entity for entity in self.entities if isinstance(entity, Item))

    def get_blocking_entity_at_location(
        self, location_x: int, location_y: int,
    ) -> Optional[Entity]:
        """특정 좌표에 이동을 막는 엔티티가 있으면 반환하고, 없으면 None을 반환합니다.

        동작 흐름:
        - 전체 entities를 순회하며 blocks_movement=True이고 좌표가 일치하는 첫 번째 엔티티 반환
        - MovementAction에서 이동 가능 여부를 확인할 때 사용
        - 시체(blocks_movement=False)는 반환하지 않으므로 시체 위로 이동 가능
        """
        for entity in self.entities:
            if (
                entity.blocks_movement
                and entity.x == location_x
                and entity.y == location_y
            ):
                return entity
        return None

    def get_actor_at_location(self, x: int, y: int) -> Optional[Actor]:
        """특정 좌표에 있는 살아있는 Actor를 반환합니다. 없으면 None을 반환합니다.

        동작 흐름:
        - actors 프로퍼티(살아있는 Actor만 포함)를 순회하며 좌표가 일치하는 Actor 반환
        - get_blocking_entity_at_location과 차이:
          Actor 타입만 반환하며, is_alive 체크가 추가로 적용됨
        - BumpAction에서 공격 대상 확인, 아이템 activate()에서 타겟 Actor 조회에 사용
        """
        for actor in self.actors:
            if actor.x == x and actor.y == y:
                return actor
        return None

    def in_bounds(self, x: int, y: int) -> bool:
        """주어진 좌표가 맵 경계 안에 있으면 True를 반환합니다.

        동작 흐름:
        - 0 ≤ x < width 이고 0 ≤ y < height 이면 True
        - MovementAction, 마우스 이벤트, 타겟 선택 등 좌표 유효성 검사에 광범위하게 사용
        """
        return 0 <= x < self.width and 0 <= y < self.height

    def render(self, console: Console) -> None:
        """맵 타일과 엔티티를 콘솔에 그립니다.

        동작 흐름 (타일 렌더링):
        1. np.select()로 세 가지 조건에 따라 타일 색상을 선택
           - visible=True  → tiles["light"]  (밝게, 현재 시야)
           - explored=True → tiles["dark"]   (어둡게, 이전에 본 곳)
           - 그 외         → tile_types.SHROUD (완전히 검정, 미탐색 영역)
        2. 결과를 console.rgb에 직접 써넣어 효율적으로 렌더링

        동작 흐름 (엔티티 렌더링):
        3. 엔티티를 render_order.value 오름차순으로 정렬
           → CORPSE(0) → ITEM(1) → ACTOR(2) 순서로 그려짐 (값이 높을수록 위에 표시)
        4. visible 배열로 현재 시야 안의 엔티티만 화면에 출력
           (시야 밖 엔티티는 어둡게 표시되는 타일과 달리 완전히 숨김)
        """
        console.rgb[0 : self.width, 0 : self.height] = np.select(
            condlist=[self.visible, self.explored],
            choicelist=[self.tiles["light"], self.tiles["dark"]],
            default=tile_types.SHROUD,
        )

        # render_order 값 오름차순으로 정렬 — 값이 낮을수록 먼저(아래에) 그려짐
        entities_sorted_for_rendering = sorted(
            self.entities, key=lambda x: x.render_order.value
        )

        # 현재 시야(visible) 안에 있는 엔티티만 화면에 출력 (시야 밖은 숨김)
        for entity in entities_sorted_for_rendering:
            if self.visible[entity.x, entity.y]:
                console.print(
                    x=entity.x, y=entity.y, text=entity.char, fg=entity.color
                )
