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

class ActionWithDirection(Action):
    def __init__(self, dx: int, dy: int):
        super().__init__()

        self.dx = dx
        self.dy = dy

    def perform(self, engine: Engine, entity: Entity) -> None:
        raise NotImplementedError()

# 공격 메서드
class MeleeAction(ActionWithDirection):
    def perform(self, engine: Engine, entity: Entity) -> None:
        dest_x = entity.x + self.dx
        dest_y = entity.y + self.dy
        target = engine.game_map.get_blocking_entity_at_location(dest_x, dest_y)
        if not target:
            return  # 공격할 엔티티가 없습니다. 

        print(f"You kick the {target.name}, much to its annoyance!")

# 동작
# action == 좌표이동(dx,dy
class MovementAction(ActionWithDirection):
    def perform(self, engine: Engine, entity: Entity) -> None:
        dest_x = entity.x + self.dx
        dest_y = entity.y + self.dy

        # 좌표가 맵 안에 있는지 확인
        if not engine.game_map.in_bounds(dest_x, dest_y):
            return  # 목적지가 경계를 벗어났습니다.
        
        # 좌표가 걸을 수 있는지(벽) 확인
        if not engine.game_map.tiles["walkable"][dest_x, dest_y]:
            return  # 목적지가 타일로 막혀 있습니다.
        
        # 좌표가 목표(엔티티)에 닿았는지 확인
        if engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            return  # 목적지가 엔티티에 의해 막혀 있습니다. 
        entity.move(self.dx, self.dy)    

# 목적지 충돌 시 
class BumpAction(ActionWithDirection):
    def perform(self, engine: Engine, entity: Entity) -> None:
        dest_x = entity.x + self.dx
        dest_y = entity.y + self.dy

        # MeleeAction와 MovementAction 클래스 중 어떤 클래스를 반환할지 
        if engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            return MeleeAction(self.dx, self.dy).perform(engine, entity)
        else:
            return MovementAction(self.dx, self.dy).perform(engine, entity)