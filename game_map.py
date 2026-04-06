import numpy as np  # type: ignore
from tcod.console import Console

import tile_types


class GameMap:
    # 정수값을 할당 받아 width와 hight를 설정.
    def __init__(self, width: int, height: int):
        self.width, self.height = width, height

        # np.full(크기, 채울값)
        self.tiles = np.full((width, height), fill_value=tile_types.floor, order="F") # order은 x와y변수의 순서를 변경. 기본은 [y,x]. order = "F" 일 시 [x,y]로 변경

        # 가로 3칸짜리 벽 생성.  x = 30,31,32 y = 22 
        # (30,22) █
        # (31,22) █
        # (32,22) █
        self.tiles[30:33, 22] = tile_types.wall

    # 플레이어 이동 제한
    def in_bounds(self, x: int, y: int) -> bool:
        """x와 y가 이 지도의 경계 내에 있으면 True를 반환합니다."""
        # 하나라도 벗어나면 false
        return 0 <= x < self.width and 0 <= y < self.height
    
    # NumPy 배열을 통째로 콘솔에 복사
    # self.tiles ->["dark"] 필드만 추출 ->콘솔 버퍼에 한 번에 복사 -> 화면 출력
    def render(self, console: Console) -> None:
        console.tiles_rgb[0:self.width, 0:self.height] = self.tiles["dark"]