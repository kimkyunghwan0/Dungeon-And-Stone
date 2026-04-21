from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

import color
import exceptions

if TYPE_CHECKING:
    from engine import Engine
    from entity import Actor, Entity, Item

# 모든 액션의 기본 클래스. 키 입력 → 액션 객체 생성 → perform() 호출 순서로 동작
class Action:
    def __init__(self, entity: Actor) -> None:
        # 이 액션을 수행할 주체(플레이어 또는 몬스터)를 저장
        super().__init__()
        self.entity = entity

    @property
    def engine(self) -> Engine:
        """이 액션이 속한 엔진을 반환합니다.

        entity → entity.parent(GameMap) → gamemap.engine 순으로 참조를 따라 올라감.
        액션 안에서 self.engine으로 게임 전체 상태에 접근할 수 있게 해주는 단축 경로.
        """
        return self.entity.gamemap.engine

    def perform(self) -> None:
        """액션을 실행합니다. 하위 클래스에서 반드시 재정의해야 합니다.

        self.engine : 이 액션이 실행되는 게임 엔진
        self.entity : 이 액션을 수행하는 주체 (플레이어 또는 몬스터)
        """
        raise NotImplementedError()


# 아이템 줍기
class PickupAction(Action):
    """발 아래 아이템을 줍고 인벤토리에 추가합니다. 인벤토리가 가득 찼으면 실패합니다."""

    def __init__(self, entity: Actor):
        super().__init__(entity)

    def perform(self) -> None:
        """동작 흐름:
        1. 현재 엔티티(플레이어)의 좌표와 인벤토리를 가져옴
        2. 게임 맵의 모든 아이템을 순회하며 같은 좌표의 아이템을 찾음
        3. 인벤토리가 가득 찼으면 Impossible 예외 발생 (줍기 실패)
        4. 아이템을 맵 엔티티 목록에서 제거하고 인벤토리에 추가
        5. 같은 좌표의 아이템이 없으면 Impossible 예외 발생
        """
        actor_location_x = self.entity.x
        actor_location_y = self.entity.y
        inventory = self.entity.inventory

        for item in self.engine.game_map.items:
            if actor_location_x == item.x and actor_location_y == item.y:
                if len(inventory.items) >= inventory.capacity:
                    # raise exceptions.Impossible("인벤토리가 가득 찼습니다.")
                    raise exceptions.Impossible("Your inventory is full.")

                # 맵에서 아이템을 떼어내고 인벤토리로 소속을 옮김
                self.engine.game_map.entities.remove(item)
                item.parent = self.entity.inventory
                inventory.items.append(item)

                # self.engine.message_log.add_message(f"{item.name}을(를) 주웠다!")
                self.engine.message_log.add_message(f"You picked up the {item.name}!")
                return

        # raise exceptions.Impossible("여기에는 아무것도 없습니다.")
        raise exceptions.Impossible("There is nothing here to pick up.")


# 아이템 사용
class ItemAction(Action):
    def __init__(
        self, entity: Actor, item: Item, target_xy: Optional[Tuple[int, int]] = None
    ):
        """동작 흐름:
        - entity : 아이템을 사용하는 액터
        - item   : 사용할 아이템 객체
        - target_xy : 타겟 좌표. 지정하지 않으면 사용자 자신의 위치를 기본 타겟으로 사용
                      (회복 포션처럼 자신에게 쓰는 아이템의 경우)
        """
        super().__init__(entity)
        self.item = item
        if not target_xy:
            target_xy = entity.x, entity.y  # 타겟 없으면 자기 자신 위치
        self.target_xy = target_xy

    @property
    def target_actor(self) -> Optional[Actor]:
        """이 액션의 목적지에 있는 Actor를 반환합니다. 없으면 None.

        target_xy 좌표에 살아있는 Actor가 있는지 맵에서 조회.
        번개 스크롤 등 특정 적을 타겟으로 하는 아이템에서 사용.
        """
        return self.engine.game_map.get_actor_at_location(*self.target_xy)

    def perform(self) -> None:
        """아이템의 효과를 발동합니다.

        consumable.activate(self)를 호출해 실제 효과 처리를 아이템에 위임.
        self(ItemAction) 자체를 컨텍스트로 전달하므로 아이템이 사용자/타겟 정보를 알 수 있음.
        """
        self.item.consumable.activate(self)


# 아이템 버리기
class DropItem(ItemAction):
    def perform(self) -> None:
        """인벤토리에서 아이템을 제거하고 현재 위치 맵에 내려놓습니다.

        실제 처리는 Inventory.drop()에 위임.
        아이템은 버린 위치의 맵 엔티티로 다시 등록되어 다시 주울 수 있음.
        """
        self.entity.inventory.drop(self.item)


# 아무 행동도 하지 않고 한 턴을 소비
class WaitAction(Action):
    def perform(self) -> None:
        """아무것도 하지 않습니다.

        턴만 소비하고 싶을 때 사용 ('.' 키 또는 숫자패드 5).
        적들은 여전히 자신의 턴을 가지므로 시간이 흐름.
        """
        pass


# 방향(dx, dy)이 있는 액션의 기본 클래스. 이동/공격 등 방향이 필요한 액션이 상속받음
class ActionWithDirection(Action):
    def __init__(self, entity: Actor, dx: int, dy: int):
        """방향 벡터(dx, dy)를 저장합니다.

        dx : x축 이동량 (음수=왼쪽, 양수=오른쪽)
        dy : y축 이동량 (음수=위, 양수=아래)
        예) dx=-1, dy=-1 이면 좌상단 대각선 방향
        """
        super().__init__(entity)
        self.dx = dx
        self.dy = dy

    @property
    def dest_xy(self) -> Tuple[int, int]:
        """이 액션의 목적지 좌표를 반환합니다.

        현재 엔티티 위치에 방향 벡터를 더해 목적지를 계산.
        예) 플레이어가 (5,5)이고 dx=1, dy=0이면 목적지는 (6,5).
        """
        return self.entity.x + self.dx, self.entity.y + self.dy

    @property
    def blocking_entity(self) -> Optional[Entity]:
        """목적지에 이동을 막는 엔티티가 있으면 반환, 없으면 None.

        blocks_movement=True인 엔티티(살아있는 캐릭터 등)만 해당.
        시체(blocks_movement=False)는 반환하지 않음.
        """
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

    @property
    def target_actor(self) -> Optional[Actor]:
        """목적지에 있는 살아있는 Actor를 반환, 없으면 None.

        is_alive(ai가 None이 아닌 Actor)만 반환하므로 시체는 포함되지 않음.
        """
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)

    def perform(self) -> None:
        raise NotImplementedError()  # 하위 클래스에서 반드시 재정의해야 함


# 근접 공격 액션 — 이동 방향에 적이 있을 때 BumpAction이 이 액션을 호출
class MeleeAction(ActionWithDirection):
    def perform(self) -> None:
        """동작 흐름:
        1. 목적지의 Actor를 조회. 없으면 Impossible 예외.
        2. 실제 데미지 = 공격력(power) - 방어력(defense) 계산
        3. 공격자가 플레이어면 밝은 회색, 적이면 연분홍 색으로 메시지 색상 결정
        4. 데미지 > 0이면 HP를 깎음 (HP setter가 0이 되면 자동으로 die() 호출)
        5. 데미지 = 0이면 "피해를 입지 않았다" 메시지 출력 (공격이 막힘)
        """
        target = self.target_actor

        if not target:
            # raise exceptions.Impossible("공격대상이 없음.")
            raise exceptions.Impossible("Nothing to attack.")

        # 실제 데미지 = 공격력 - 방어력 (방어력이 높으면 데미지가 0이 될 수 있음)
        damage = self.entity.fighter.power - target.fighter.defense

        # 공격자가 플레이어인지 몬스터인지에 따라 메시지 색상 변경
        if self.entity is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        # attack_desc = f"{self.entity.name.capitalize()}가 {target.name}을(를) 공격!"
        attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}"
        if damage > 0:
            self.engine.message_log.add_message(
                # f"{attack_desc} {damage}만큼 피해를 입혔다."
                f"{attack_desc} for {damage} hit points.", attack_color
            )
            target.fighter.hp -= damage  # HP 감소 → 0이 되면 fighter.die() 자동 호출
        else:
            # 방어력이 공격력 이상일 때 — 공격이 막혔음을 알림
            self.engine.message_log.add_message(
                # f"{attack_desc} 하지만 피해를 입지 않았다."
                f"{attack_desc} but does no damage.", attack_color
            )


# 이동 액션 — 목적지가 유효하면 엔티티를 (dx, dy)만큼 이동
class MovementAction(ActionWithDirection):
    def perform(self) -> None:
        """동작 흐름:
        1. dest_xy로 목적지 좌표를 계산
        2. 맵 경계를 벗어나면 Impossible 예외 발생
        3. 벽 타일(walkable=False)이면 Impossible 예외 발생
        4. 이동을 막는 엔티티(적 등)가 있으면 Impossible 예외 발생
        5. 위 3가지 검사를 모두 통과하면 entity.move()로 좌표를 실제로 이동
        """
        dest_x, dest_y = self.dest_xy

        # 좌표가 맵 안에 있는지 확인
        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            # raise exceptions.Impossible("그쪽은 막혀있습니다.")  # 목적지가 맵 경계를 벗어남
            raise exceptions.Impossible("That way is blocked.")

        # 좌표가 걸을 수 있는 타일인지(벽 여부) 확인
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            # raise exceptions.Impossible("그쪽은 막혀있습니다.")  # 목적지가 벽 타일
            raise exceptions.Impossible("That way is blocked.")

        # 좌표에 이동을 막는 엔티티(적 등)가 있는지 확인
        if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            # raise exceptions.Impossible("그쪽은 막혀있습니다.")  # 다른 엔티티가 길을 막고 있음
            raise exceptions.Impossible("That way is blocked.")

        self.entity.move(self.dx, self.dy)


# 방향 입력 시 목적지 상황에 따라 이동 또는 공격을 자동으로 선택
# 플레이어가 방향키를 누를 때 항상 이 액션이 먼저 실행됨
class BumpAction(ActionWithDirection):
    def perform(self) -> None:
        """목적지 상황을 보고 MeleeAction 또는 MovementAction을 선택해 실행합니다.

        동작 흐름:
        - 목적지에 살아있는 Actor가 있으면 → MeleeAction(공격)
        - 없으면 → MovementAction(이동)

        이 분기 덕분에 플레이어는 이동과 공격을 같은 키로 처리할 수 있음.
        적의 AI도 BumpAction 대신 MeleeAction/MovementAction을 직접 호출하기도 함.
        """
        if self.target_actor:
            return MeleeAction(self.entity, self.dx, self.dy).perform()
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()
