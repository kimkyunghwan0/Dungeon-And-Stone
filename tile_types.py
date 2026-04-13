from typing import Tuple

import numpy as np  # type: ignore

# Console.rgb와 호환되는 타일 그래픽 구조화된 데이터 타입
# ch : 문자(character)를 의미하며, 정수 형태로 저장
# fg : 글자(전경) 색상
# bg : 배경색(RGB)
graphic_dt = np.dtype(
    [
        ("ch", np.int32),  # 정수를 유니코드문자(숫자)로 변환
        ("fg", "3B"),  # 3B : RGB 색상 값을 표현하기 위한 데이터 형식
        ("bg", "3B"),
    ]
)

# 정적으로 정의된 타일 데이터를 위한 Tile 구조체
# walkable : 플레이어가 이 타일 위를 이동할 수 있는지 여부
# transparent : 이 타일이 시야(Field of View, FOV)를 차단하는지 여부
# dark : 위에서 정의한 grahic_dt 타입 사용. 출력할 문자, 글자(전경)색, 배경색 정보를 포함
tile_dt = np.dtype(
    [
        ("walkable", np.bool),  # 이 타일 위를 걸을 수 있으면 True
        ("transparent", np.bool),  # 시야(FOV)를 막지 않으면 True
        ("dark", graphic_dt),  # 현재 시야 밖에 있을 때의 그래픽 정보
        ("light", graphic_dt), # 타일이 FOV에 있을 때의 그래픽
    ]
)


# 타일 하나를 구성하는 데이터를 받아서, 구조화된 numpy 배열로 만들어주는 함수
def new_tile(
    *,  # '*' 는 키워드 전용 인자. 매개변수 순서가 중요하지 않도록 키워드 사용을 강제합니다.
    walkable: int, # 해당 타일을 지나갈 수 있는지 여부 1 | 0
    transparent: int, # 시야가 통과되는지 여부 1 | 0 
    dark: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]], # 시야 밖(어두운 상태)에서의 타일 정보. [문자, 글자색, 배경색]
    light: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
) -> np.ndarray:
    """ 개별 타일 타입을 정의하기 위한 헬퍼 함수 """
    return np.array((walkable, transparent, dark, light), dtype=tile_dt) # 타일 1개를 표현하는 구조화된 numpy 데이터 생성

# 타일이 화면에 보이지 않거나 "탐색"되지 않았을 때 사용할 속성입니다. 검정색타일
SHROUD = np.array((ord(" "), (255, 255, 255), (0, 0, 0)), dtype=graphic_dt)

# 바닥 : 이동 가능, 시야 보임, 밝은색
floor = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord(" "), (255, 255, 255), (50, 50, 150)),
    light=(ord(" "), (255, 255, 255), (200, 180, 50)),
)

# 벽 : 이동 불가, 시야 차단, 어두운색
wall = new_tile(
    walkable=False,
    transparent=False,
    dark=(ord(" "), (255, 255, 255), (0, 0, 100)),
    light=(ord(" "), (255, 255, 255), (130, 110, 50)),
)