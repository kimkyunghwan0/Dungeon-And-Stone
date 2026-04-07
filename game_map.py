from __future__ import annotations

from typing import Iterable, Optional, TYPE_CHECKING

import numpy as np  # type: ignore
from tcod.console import Console

import tile_types

if TYPE_CHECKING:
    from entity import Entity

class GameMap:
    # 정수값을 할당 받아 width와 hight를 설정.
    def __init__(self, width: int, height: int, entities: Iterable[Entity] = ()):
        self.width, self.height = width, height
        self.entities = set(entities)

        # np.full(크기, 채울값)
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order="F")

        self.visible = np.full((width, height), fill_value=False, order="F") # 플레이어가 현재 볼 수 있는 타일
        self.explored = np.full((width, height), fill_value=False, order="F") # 플레이어가 이전에 본 타일

        # 가로 3칸짜리 벽 생성.  x = 30,31,32 y = 22 
        # (30,22) █
        # (31,22) █
        # (32,22) █
        self.tiles[30:33, 22] = tile_types.wall

    def get_blocking_entity_at_location(self, location_x: int, location_y: int) -> Optional[Entity]:
        # Entity를 찾으면 → Entity 반환
        # 못 찾으면     → None 반환
        for entity in self.entities:
            # entity.blocks_movement : 이동을 막는 엔티티인가?
            # entity.x == location_xX : 좌표가 일치하는가?
            # entity.y == location_yY : 좌표가 일치하는가?
            if entity.blocks_movement and entity.x == location_x and entity.y == location_y:
                return entity

        return None
    
    # 플레이어 이동 제한
    def in_bounds(self, x: int, y: int) -> bool:
        """x와 y가 이 지도의 경계 내에 있으면 True를 반환합니다."""
        # 하나라도 벗어나면 false
        return 0 <= x < self.width and 0 <= y < self.height
    
    # NumPy 배열을 통째로 콘솔에 복사
    # 1. self.tiles ->["dark"] 필드만 추출 ->콘솔 버퍼에 한 번에 복사 -> 화면 출력
    # 2. --> np.select를 사용하면 콘드리스트에 지정된 내용을 기반으로 원하는 타일을 조건부로 그릴 수 있습
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
            # FOV 내에 있는 엔티티만 출력
            if self.visible[entity.x, entity.y]:
                console.print(x=entity.x, y=entity.y, string=entity.char, fg=entity.color)