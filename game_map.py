from __future__ import annotations

from typing import Iterable, Optional, TYPE_CHECKING

import numpy as np  # type: ignore
from tcod.console import Console

import tile_types

if TYPE_CHECKING:
    from entity import Entity

# 맵 전체 정보(타일, 엔티티, 시야)를 관리하는 클래스
class GameMap:
    # width, height : 맵 크기 / entities : 맵에 배치할 초기 엔티티 목록
    def __init__(self, width: int, height: int, entities: Iterable[Entity] = ()):
        self.width, self.height = width, height
        self.entities = set(entities)  # 중복 없는 엔티티 집합

        # np.full(크기, 채울값) — 맵 전체를 기본값(벽)으로 초기화
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order="F")

        self.visible = np.full((width, height), fill_value=False, order="F")   # 플레이어가 현재 볼 수 있는 타일
        self.explored = np.full((width, height), fill_value=False, order="F")  # 플레이어가 이전에 본 타일

    # 특정 위치에 이동을 막는 엔티티가 있으면 반환, 없으면 None 반환
    def get_blocking_entity_at_location(self, location_x: int, location_y: int) -> Optional[Entity]:
        for entity in self.entities:
            # blocks_movement가 True이고 좌표가 일치하는 엔티티를 찾음
            if entity.blocks_movement and entity.x == location_x and entity.y == location_y:
                return entity

        return None

    # 주어진 좌표가 맵 경계 안에 있는지 확인
    def in_bounds(self, x: int, y: int) -> bool:
        """x와 y가 이 지도의 경계 내에 있으면 True를 반환합니다."""
        return 0 <= x < self.width and 0 <= y < self.height  # 하나라도 벗어나면 False

    # 맵 타일과 엔티티를 콘솔에 그림
    # np.select를 사용해 visible/explored 상태에 따라 타일 색상을 조건부로 선택
    def render(self, console: Console) -> None:
        """
            맵을 렌더링합니다.
            타일이 "visible" 배열에 있으면 "light" 색상으로 그립니다.
            "visible" 배열에 없지만 "explored" 배열에 있으면 "dark" 색상으로 그립니다.
            그렇지 않으면 기본값은 "SHROUD"입니다.
        """
        console.tiles_rgb[0:self.width, 0:self.height] = np.select(
            condlist=[self.visible, self.explored],
            choicelist=[self.tiles["light"], self.tiles["dark"]],
            default=tile_types.SHROUD
        )

        for entity in self.entities:
            # FOV 내에 있는 엔티티만 출력 (시야 밖 엔티티는 숨김)
            if self.visible[entity.x, entity.y]:
                console.print(x=entity.x, y=entity.y, string=entity.char, fg=entity.color)