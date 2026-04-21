from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import actions
import color
import components.ai
import components.inventory
from components.base_component import BaseComponent
from exceptions import Impossible
from input_handlers import (
    ActionOrHandler,
    AreaRangedAttackHandler,
    SingleRangedAttackHandler,
)

if TYPE_CHECKING:
    from entity import Actor, Item


# 사용 가능한 아이템(소비 아이템)의 기본 클래스
class Consumable(BaseComponent):
    parent: Item

    def get_action(self, consumer: Actor) -> Optional[ActionOrHandler]:
        """이 아이템 사용에 필요한 액션을 반환합니다.

        동작 흐름:
        - 기본 구현은 자기 자신을 타겟으로 하는 ItemAction을 바로 반환.
        - 회복 포션처럼 타겟 선택이 필요 없는 아이템에 적합.
        - 혼란/번개/파이어볼처럼 타겟 선택이 필요한 아이템은 이 메서드를 오버라이드해
          이벤트 핸들러를 교체한 뒤 None을 반환함
          (None 반환 → 이 턴에 즉시 행동이 실행되지 않고 타겟 선택 화면으로 전환).
        """
        return actions.ItemAction(consumer, self.parent)

    def activate(self, action: actions.ItemAction) -> None:
        """아이템 효과를 발동합니다.

        action 객체에 사용자(entity), 타겟 좌표(target_xy), 타겟 액터(target_actor) 등
        효과 처리에 필요한 컨텍스트 정보가 담겨 있음.
        서브클래스에서 반드시 구현해야 합니다.
        """
        raise NotImplementedError()

    def consume(self) -> None:
        """사용된 아이템을 인벤토리에서 제거합니다.

        동작 흐름:
        1. self.parent(Item 엔티티)의 parent(Inventory)를 조회
        2. 해당 parent가 Inventory 인스턴스인 경우에만 items 목록에서 제거
           (맵에 있는 아이템에 실수로 호출되는 경우를 방어)
        아이템 효과가 성공적으로 발동된 직후 호출해 인벤토리를 소비함.
        """
        entity = self.parent
        inventory = entity.parent
        if isinstance(inventory, components.inventory.Inventory):
            inventory.items.remove(entity)


# 혼란 스크롤 — 타겟 적에게 지정된 턴 수만큼 혼란 상태이상을 부여
class ConfusionConsumable(Consumable):
    def __init__(self, number_of_turns: int):
        self.number_of_turns = number_of_turns  # 혼란 지속 턴 수

    def get_action(self, consumer: Actor) -> SingleRangedAttackHandler:
        """타겟 선택 화면으로 전환하고 None을 반환합니다.

        동작 흐름:
        1. 메시지 로그에 타겟 선택 안내 메시지 출력
        2. 이벤트 핸들러를 SingleRangedAttackHandler로 교체
           → 커서로 맵 위의 한 지점을 선택하는 화면으로 전환됨
        3. callback: 선택된 좌표(xy)로 ItemAction을 생성하는 람다 함수
           → 플레이어가 타겟을 확인하면 callback이 실행되어 activate()까지 이어짐
        4. None 반환 → 이 턴에 즉시 행동이 실행되지 않음
        """
        self.engine.message_log.add_message(
            # "타겟을 선택하세요."
            "Select a target.", color.needs_target
        )
        return SingleRangedAttackHandler(
            self.engine,
            callback=lambda xy: actions.ItemAction(consumer, self.parent, xy),
        )

    def activate(self, action: actions.ItemAction) -> None:
        """선택된 타겟에 혼란 상태이상을 부여합니다.

        동작 흐름:
        1. 타겟 좌표가 현재 시야 안에 있는지 확인 (시야 밖이면 Impossible)
        2. 타겟 좌표에 살아있는 Actor가 있는지 확인 (없으면 Impossible)
        3. 타겟이 사용자 자신인지 확인 (자기 자신에게 사용 불가)
        4. 타겟의 ai를 ConfusedEnemy로 교체
           - previous_ai에 원래 AI를 저장해 두어 나중에 복원 가능하도록 함
           - turns_remaining만큼 혼란 상태가 지속됨
        5. consume()으로 아이템을 인벤토리에서 제거
        """
        consumer = action.entity
        target = action.target_actor

        if not self.engine.game_map.visible[action.target_xy]:
            # raise Impossible("시야 밖은 타겟으로 지정할 수 없습니다.")
            raise Impossible("You cannot target an area that you cannot see.")
        if not target:
            # raise Impossible("타겟으로 지정할 적이 없습니다.")
            raise Impossible("You must select an enemy to target.")
        if target is consumer:
            # raise Impossible("자기 자신에게는 사용할 수 없습니다!")
            raise Impossible("You cannot confuse yourself!")

        self.engine.message_log.add_message(
            # f"{target.name}의 눈빛이 흐려지며 비틀거리기 시작한다!"
            f"{target.name}'s eyes glaze over as it stumbles around!",
            color.status_effect_applied,
        )
        target.ai = components.ai.ConfusedEnemy(
            entity=target, previous_ai=target.ai, turns_remaining=self.number_of_turns,
        )
        self.consume()


# 파이어볼 스크롤 — 지정한 지점을 중심으로 반경 내 모든 엔티티에게 피해를 줌
class FireballDamageConsumable(Consumable):
    def __init__(self, damage: int, radius: int):
        self.damage = damage  # 피해량
        self.radius = radius  # 범위 반경 (타일 단위)

    def get_action(self, consumer: Actor) -> AreaRangedAttackHandler:
        """범위 타겟 선택 화면으로 전환하고 None을 반환합니다.

        동작 흐름:
        1. 메시지 로그에 타겟 선택 안내 메시지 출력
        2. 이벤트 핸들러를 AreaRangedAttackHandler로 교체
           → 커서 주변에 범위(radius)를 표시하는 선택 화면으로 전환됨
        3. 타겟이 확인되면 callback으로 ItemAction을 생성해 activate()까지 연결
        4. None 반환 → 이 턴에 즉시 행동이 실행되지 않음
        """
        self.engine.message_log.add_message(
            # "타겟 지점을 선택하세요."
            "Select a target location.", color.needs_target
        )
        return AreaRangedAttackHandler(
            self.engine,
            radius=self.radius,
            callback=lambda xy: actions.ItemAction(consumer, self.parent, xy),
        )

    def activate(self, action: actions.ItemAction) -> None:
        """선택된 좌표 반경 내 모든 Actor에게 피해를 줍니다.

        동작 흐름:
        1. 타겟 좌표가 시야 안에 있는지 확인 (시야 밖이면 Impossible)
        2. 맵의 모든 살아있는 Actor를 순회
           - actor.distance(*target_xy) ≤ radius 이면 범위 안으로 판정
           - 플레이어도 범위 안에 있으면 피해를 받음 (아군 피해 있음)
        3. 범위 안 Actor에게 take_damage()로 방어력 무시 피해 적용
        4. 범위 안에 아무도 없으면 Impossible 예외 발생 (아이템 소비 안 함)
        5. 성공하면 consume()으로 아이템 제거
        """
        target_xy = action.target_xy

        if not self.engine.game_map.visible[target_xy]:
            # raise Impossible("시야 밖은 타겟으로 지정할 수 없습니다.")
            raise Impossible("You cannot target an area that you cannot see.")

        targets_hit = False
        for actor in self.engine.game_map.actors:
            if actor.distance(*target_xy) <= self.radius:
                self.engine.message_log.add_message(
                    # f"{actor.name}이(가) 불길에 휩싸여 {self.damage}의 피해를 입었다!"
                    f"The {actor.name} is engulfed in a fiery explosion, taking {self.damage} damage!"
                )
                actor.fighter.take_damage(self.damage)
                targets_hit = True

        if not targets_hit:
            # raise Impossible("범위 내 대상이 없습니다.")
            raise Impossible("There are no targets in the radius.")
        self.consume()


# 회복 포션 — 사용자의 HP를 amount만큼 회복
class HealingConsumable(Consumable):
    def __init__(self, amount: int):
        self.amount = amount  # 최대 회복량

    def activate(self, action: actions.ItemAction) -> None:
        """사용자의 HP를 회복합니다.

        동작 흐름:
        1. consumer(사용자)의 fighter.heal()을 호출해 amount만큼 회복 시도
        2. heal()은 실제 회복량을 반환 (이미 HP 최대치면 0 반환)
        3. 실제 회복량이 0보다 크면 성공 메시지 출력 후 아이템 소비
        4. 회복량이 0이면 (이미 최대 체력) Impossible 예외 발생 → 아이템 소비 안 함
        """
        consumer = action.entity
        amount_recovered = consumer.fighter.heal(self.amount)

        if amount_recovered > 0:
            self.engine.message_log.add_message(
                # f"{self.parent.name}을(를) 사용해 체력을 {amount_recovered} 회복했다!"
                f"You consume the {self.parent.name}, and recover {amount_recovered} HP!",
                color.health_recovered,
            )
            self.consume()
        else:
            # raise Impossible("당신은 이미 건강합니다.")
            raise Impossible("Your health is already full.")


# 번개 스크롤 — 시야 내 가장 가까운 적에게 번개 피해를 줌
class LightningDamageConsumable(Consumable):
    def __init__(self, damage: int, maximum_range: int):
        self.damage = damage                # 피해량
        self.maximum_range = maximum_range  # 최대 사정거리 (이 거리 밖의 적은 타겟이 안 됨)

    def activate(self, action: actions.ItemAction) -> None:
        """시야 안에서 사용자와 가장 가까운 적에게 번개 피해를 줍니다.

        동작 흐름:
        1. closest_distance를 maximum_range + 1로 초기화 (사정거리 밖은 후보 제외)
        2. 맵의 모든 살아있는 Actor를 순회
           - 사용자 자신이 아니고, 현재 시야 안에 있는 Actor만 후보
           - 사용자와의 유클리드 거리가 closest_distance보다 가까우면 target 갱신
        3. 가장 가까운 타겟이 존재하면 take_damage()로 피해 적용 후 아이템 소비
        4. 사정거리 내 적이 없으면 Impossible 예외 발생 → 아이템 소비 안 함

        타겟 선택 화면 없이 자동으로 가장 가까운 적을 선택하는 점이 특징.
        """
        consumer = action.entity
        target = None
        closest_distance = self.maximum_range + 1.0  # 이 값보다 멀면 후보 제외

        for actor in self.engine.game_map.actors:
            if actor is not consumer and self.parent.gamemap.visible[actor.x, actor.y]:
                distance = consumer.distance(actor.x, actor.y)

                if distance < closest_distance:
                    target = actor
                    closest_distance = distance

        if target:
            self.engine.message_log.add_message(
                # f"번개가 {target.name}에게 내리쳐 {self.damage}의 피해를 입혔다!"
                f"A lightning bolt strikes the {target.name} with a loud thunder, for {self.damage} damage!"
            )
            target.fighter.take_damage(self.damage)
            self.consume()
        else:
            # raise Impossible("사정거리 내 적이 없습니다.")
            raise Impossible("No enemy is close enough to strike.")
