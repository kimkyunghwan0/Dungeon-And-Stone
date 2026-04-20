from __future__ import annotations

from typing import TYPE_CHECKING

import color

if TYPE_CHECKING:
    from tcod import Console
    from engine import Engine
    from game_map import GameMap


def get_names_at_location(x: int, y: int, game_map: GameMap) -> str:
    """특정 좌표에 있는 모든 엔티티의 이름을 쉼표로 연결해 반환합니다.

    동작 흐름:
    1. 좌표가 맵 경계를 벗어나거나 현재 시야(visible) 밖이면 빈 문자열 반환
    2. game_map.entities 전체를 순회하며 해당 좌표의 엔티티 이름을 수집
    3. 이름들을 ", "로 연결하고 첫 글자를 대문자로 변환해 반환
       예) "Orc, Troll" 또는 "Health Potion"

    마우스 호버 시 커서 위치의 엔티티 이름을 표시하는 데 사용.
    시야 밖이면 엔티티가 있어도 이름을 표시하지 않음.
    """
    if not game_map.in_bounds(x, y) or not game_map.visible[x, y]:
        return ""

    # 해당 좌표의 모든 엔티티 이름을 ", "로 연결
    names = ", ".join(
        entity.name for entity in game_map.entities if entity.x == x and entity.y == y
    )

    return names.capitalize()  # 첫 글자를 대문자로


def render_bar(
    console: Console, current_value: int, maximum_value: int, total_width: int
) -> None:
    """화면 왼쪽 하단(y=45)에 HP 바를 렌더링합니다.

    동작 흐름:
    1. 현재 HP 비율(current_value / maximum_value)로 채워진 바의 너비(bar_width) 계산
    2. draw_rect()로 전체 바 영역을 빈 색(어두운 빨강, bar_empty)으로 먼저 채움
    3. bar_width > 0이면 같은 위치에 채워진 색(초록, bar_filled)으로 덮어씌움
       → 두 색이 겹쳐 HP 비율에 따라 초록/빨강 바가 표시됨
    4. 바 위에 "HP: 현재/최대" 형태의 텍스트를 흰색으로 출력

    예) HP 20/30이면 bar_width = 13, 전체 20칸 중 13칸이 초록으로 채워짐.
    """
    # 현재 HP 비율에 따라 채워진 바의 픽셀(타일) 너비 계산
    bar_width = int(float(current_value) / maximum_value * total_width)

    # 바 전체 영역을 빈 색(어두운 빨강)으로 먼저 채움
    console.draw_rect(x=0, y=45, width=total_width, height=1, ch=1, bg=color.bar_empty)

    # HP가 남아있으면 채워진 색(초록)으로 덮어씌움
    if bar_width > 0:
        console.draw_rect(
            x=0, y=45, width=bar_width, height=1, ch=1, bg=color.bar_filled
        )

    # HP 수치를 바 위에 텍스트로 출력 (예: "HP: 20/30")
    console.print(
        x=1, y=45, text=f"HP: {current_value}/{maximum_value}", fg=color.bar_text
    )


def render_names_at_mouse_location(
    console: Console, x: int, y: int, engine: Engine
) -> None:
    """마우스 커서가 위치한 타일의 엔티티 이름을 화면에 출력합니다.

    동작 흐름:
    1. engine.mouse_location에서 현재 마우스 커서의 맵 좌표를 가져옴
       (마우스 이동 이벤트마다 EventHandler.ev_mousemotion()이 갱신함)
    2. get_names_at_location()으로 해당 좌표의 엔티티 이름 문자열 생성
    3. console.print()로 (x, y) 위치에 출력
       - 시야 밖이거나 엔티티가 없으면 빈 문자열이 출력됨 (아무것도 표시 안 됨)

    engine.render()에서 매 프레임 호출되어 마우스 위치를 실시간으로 반영.
    """
    mouse_x, mouse_y = engine.mouse_location

    names_at_mouse_location = get_names_at_location(
        x=mouse_x, y=mouse_y, game_map=engine.game_map
    )

    console.print(x=x, y=y, text=names_at_mouse_location)
