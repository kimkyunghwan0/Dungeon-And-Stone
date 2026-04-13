from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

import color

if TYPE_CHECKING:
    from engine import Engine
    from entity import Actor, Entity

# 모든 액션의 기본 클래스. 키 입력 → 액션 객체 생성 → perform() 호출 순서로 동작
class Action:
    def __init__(self, entity: Actor) -> None:
        super().__init__()
        self.entity = entity  # 이 액션을 수행하는 엔티티

    @property
    def engine(self) -> Engine:
        """이 액션이 속한 엔진을 반환합니다. (엔티티 → 맵 → 엔진 경로로 접근)"""
        return self.entity.gamemap.engine

    def perform(self) -> None:
        """액션을 실행합니다. 하위 클래스에서 반드시 재정의해야 합니다.

        self.engine : 이 액션이 실행되는 게임 엔진
        self.entity : 이 액션을 수행하는 주체 (플레이어 또는 몬스터)
        """
        raise NotImplementedError()

# Esc 키 입력 시 실행 — 게임 종료
class EscapeAction(Action):
     def perform(self) -> None:
        raise SystemExit()

# 아무 행동도 하지 않고 한 턴을 소비
class WaitAction(Action):
    def perform(self) -> None:
        pass

# 방향(dx, dy)이 있는 액션의 기본 클래스. 이동/공격 등 방향이 필요한 액션이 상속받음
class ActionWithDirection(Action):
    # dx : x축 이동량 , dy : y축 이동량 (예: dx=-1이면 왼쪽, dy=-1이면 위쪽)
    def __init__(self, entity: Actor, dx: int, dy: int):
        super().__init__(entity)
        self.dx = dx
        self.dy = dy

    @property
    def dest_xy(self) -> Tuple[int, int]:
        """이 액션의 목적지 좌표를 반환합니다. (현재 위치 + 이동 방향)"""
        return self.entity.x + self.dx, self.entity.y + self.dy

    @property
    def blocking_entity(self) -> Optional[Entity]:
        """목적지에 이동을 막는 엔티티가 있으면 반환, 없으면 None."""
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

    @property
    def target_actor(self) -> Optional[Actor]:
        """목적지에 있는 Actor(살아있는 캐릭터)를 반환, 없으면 None."""
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)

    def perform(self) -> None:
        raise NotImplementedError()  # 하위 클래스에서 반드시 재정의해야 함

# 근접 공격 액션 — 이동 방향에 적이 있을 때 BumpAction이 이 액션을 호출
class MeleeAction(ActionWithDirection):
    def perform(self) -> None:
        target = self.target_actor

        if not target:
            return  # 공격할 엔티티가 없으면 아무것도 하지 않음

        # 실제 데미지 = 공격력 - 방어력 (방어력이 높으면 데미지가 0이 될 수 있음)
        damage = self.entity.fighter.power - target.fighter.defense

        # 공격자가 플레이어인지 몬스터인지에 따라 메시지 색상 변경
        if self.entity is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        attack_desc = f"{self.entity.name.capitalize()}가 {target.name}을(를) 공격!"
        if damage > 0:
            self.engine.message_log.add_message(
                f"{attack_desc} {damage}만큼 피해를 입혔다.", attack_color
            )
            target.fighter.hp -= damage  # HP 감소 → 0이 되면 fighter.die() 자동 호출
        else:
            # 방어력이 공격력 이상일 때 — 공격이 막혔음을 알림
            self.engine.message_log.add_message(
                f"{attack_desc} 하지만 피해를 입지 않았다.", attack_color
            )

# 이동 액션 — 목적지가 유효하면 엔티티를 (dx, dy)만큼 이동
class MovementAction(ActionWithDirection):
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy

        # 좌표가 맵 안에 있는지 확인
        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            return  # 목적지가 맵 경계를 벗어남

        # 좌표가 걸을 수 있는 타일인지(벽 여부) 확인
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            return  # 목적지가 벽 타일

        # 좌표에 이동을 막는 엔티티(적 등)가 있는지 확인
        if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            return  # 다른 엔티티가 길을 막고 있음

        self.entity.move(self.dx, self.dy)

# 방향 입력 시 목적지 상황에 따라 이동 또는 공격을 자동으로 선택
# 플레이어가 방향키를 누를 때 항상 이 액션이 먼저 실행됨
class BumpAction(ActionWithDirection):
    def perform(self) -> None:
        # 목적지에 Actor가 있으면 → 공격, 없으면 → 이동
        if self.target_actor:
            return MeleeAction(self.entity, self.dx, self.dy).perform()
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()
