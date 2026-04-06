from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity

# 액션
class Action:
    def perform(self, engine: Engine, entity: Entity) -> None:
        """범위를 결정하는 데 필요한 객체를 사용하여 이 작업을 수행합니다.

        '엔진'은 이 작업이 수행되고 있는 범위입니다.

        'entity'는 그 행동을 수행하는 객체입니다.

        이 메서드는 Action 하위 클래스에 의해 재정의되어야 합니다.
        """
        raise NotImplementedError()

# Esc 키 
# 시스템 종료
class EscapeAction(Action):
    def perform(self, engine: Engine, entity: Entity) -> None:
        raise SystemExit()

# 동작
# action == 좌표이동(dx,dy
class MovementAction(Action):
    def __init__(self, dx: int, dy: int):
        super().__init__()

        self.dx = dx
        self.dy = dy

    def perform(self, engine: Engine, entity: Entity) -> None:
        dest_x = entity.x + self.dx
        dest_y = entity.y + self.dy

        # 좌표가 맵 안에 있는지 확인
        if not engine.game_map.in_bounds(dest_x, dest_y):
            return  # 목적지가 경계를 벗어났습니다.
        # 좌표가 걸을 수 있는지(벽) 확인
        if not engine.game_map.tiles["walkable"][dest_x, dest_y]:
            return  # 목적지가 타일로 막혀 있습니다.

        entity.move(self.dx, self.dy)    