from __future__ import annotations

from typing import TYPE_CHECKING

import color

if TYPE_CHECKING:
    from tcod import Console
    from engine import Engine
    from game_map import GameMap


# 특정 좌표에 있는 모든 엔티티의 이름을 쉼표로 연결해 반환
# 좌표가 맵 밖이거나 현재 시야 밖이면 빈 문자열 반환
def get_names_at_location(x: int, y: int, game_map: GameMap) -> str:
    if not game_map.in_bounds(x, y) or not game_map.visible[x, y]:
        return ""

    # 해당 좌표의 모든 엔티티 이름을 ", "로 연결
    names = ", ".join(
        entity.name for entity in game_map.entities if entity.x == x and entity.y == y
    )

    return names.capitalize()  # 첫 글자를 대문자로


# 화면 왼쪽 하단(y=45)에 HP 바를 렌더링하는 함수
# 전체 바를 빈 색(bar_empty)으로 깔고, HP 비율만큼 채운 색(bar_filled)으로 덮어씌움
def render_bar(
    console: Console, current_value: int, maximum_value: int, total_width: int
) -> None:
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


# 마우스가 올라간 타일의 엔티티 이름을 화면에 출력
# 시야 밖이거나 엔티티가 없으면 빈 문자열이 출력됨 (아무것도 표시 안 됨)
def render_names_at_mouse_location(
    console: Console, x: int, y: int, engine: Engine
) -> None:
    mouse_x, mouse_y = engine.mouse_location

    names_at_mouse_location = get_names_at_location(
        x=mouse_x, y=mouse_y, game_map=engine.game_map
    )

    console.print(x=x, y=y, text=names_at_mouse_location)
