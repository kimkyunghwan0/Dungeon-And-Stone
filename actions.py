from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity

# 모든 액션의 기본 클래스. 키 입력 → 액션 객체 생성 → perform() 호출 순서로 동작
class Action:
    def perform(self, engine: Engine, entity: Entity) -> None:
        """범위를 결정하는 데 필요한 객체를 사용하여 이 작업을 수행합니다.

        '엔진'은 이 작업이 수행되고 있는 범위입니다.

        'entity'는 그 행동을 수행하는 객체입니다.

        이 메서드는 Action 하위 클래스에 의해 재정의되어야 합니다.
        """
        raise NotImplementedError()

# Esc 키 입력 시 실행 — 게임 종료
class EscapeAction(Action):
    def perform(self, engine: Engine, entity: Entity) -> None:
        raise SystemExit()

# 방향(dx, dy)이 있는 액션의 기본 클래스. 이동/공격 등 방향이 필요한 액션이 상속받음
class ActionWithDirection(Action):
    # dx : x축 이동량 , dy : y축 이동량 (예: dx=-1이면 왼쪽, dy=-1이면 위쪽)
    def __init__(self, dx: int, dy: int):
        super().__init__()

        self.dx = dx
        self.dy = dy

    def perform(self, engine: Engine, entity: Entity) -> None:
        raise NotImplementedError()  # 하위 클래스에서 반드시 재정의해야 함

# 근접 공격 액션 — 이동 방향에 적이 있을 때 BumpAction이 이 액션을 호출
class MeleeAction(ActionWithDirection):
    def perform(self, engine: Engine, entity: Entity) -> None:
        dest_x = entity.x + self.dx
        dest_y = entity.y + self.dy
        target = engine.game_map.get_blocking_entity_at_location(dest_x, dest_y)
        if not target:
            return  # 공격할 엔티티가 없습니다.

        print(f"You kick the {target.name}, much to its annoyance!")

# 이동 액션 — 목적지가 유효하면 엔티티를 (dx, dy)만큼 이동
class MovementAction(ActionWithDirection):
    def perform(self, engine: Engine, entity: Entity) -> None:
        dest_x = entity.x + self.dx
        dest_y = entity.y + self.dy

        # 좌표가 맵 안에 있는지 확인
        if not engine.game_map.in_bounds(dest_x, dest_y):
            return  # 목적지가 경계를 벗어났습니다.

        # 좌표가 걸을 수 있는 타일인지(벽 여부) 확인
        if not engine.game_map.tiles["walkable"][dest_x, dest_y]:
            return  # 목적지가 벽으로 막혀 있습니다.

        # 좌표에 이동을 막는 엔티티(적 등)가 있는지 확인
        if engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            return  # 목적지가 엔티티에 의해 막혀 있습니다.

        entity.move(self.dx, self.dy)

# 방향 입력 시 목적지 상황에 따라 이동 또는 공격을 자동으로 선택
class BumpAction(ActionWithDirection):
    def perform(self, engine: Engine, entity: Entity) -> None:
        dest_x = entity.x + self.dx
        dest_y = entity.y + self.dy

        # 목적지에 엔티티가 있으면 공격, 없으면 이동
        if engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            return MeleeAction(self.dx, self.dy).perform(engine, entity)
        else:
            return MovementAction(self.dx, self.dy).perform(engine, entity)
