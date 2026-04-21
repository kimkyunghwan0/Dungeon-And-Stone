from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent
from render_order import RenderOrder
import color

if TYPE_CHECKING:
    from entity import Actor

# 전투 관련 스탯(HP, 방어력, 공격력)을 담당하는 컴포넌트
# Entity에 직접 넣지 않고 분리한 이유: 나중에 아이템이나 버프로 스탯을 수정하기 쉬움
class Fighter(BaseComponent):
    parent: Actor

    def __init__(self, hp: int, defense: int, power: int):
        """전투 스탯을 초기화합니다.

        매개변수:
        - hp     : 최대 체력이자 초기 체력. 내부적으로 max_hp와 _hp 두 값으로 관리.
        - defense: 방어력. 받는 데미지에서 차감됨 (실제 데미지 = power - defense).
        - power  : 공격력. 상대 defense를 뺀 값이 실제 데미지.

        _hp를 프라이빗으로 관리하는 이유:
        hp setter에서 클램핑(0~max_hp 범위 유지)과 사망 처리를 자동화하기 위함.
        외부에서 hp를 직접 수정하면 setter가 실행되어 항상 안전하게 처리됨.
        """
        self.max_hp = hp
        self._hp = hp      # 실제 HP는 _hp(프라이빗)로 관리, 외부에서는 hp 프로퍼티로 접근
        self.defense = defense
        self.power = power

    @property
    def hp(self) -> int:
        """현재 HP를 반환합니다 (읽기 전용 접근점)."""
        return self._hp

    @hp.setter
    def hp(self, value: int) -> None:
        """HP를 변경할 때 자동으로 범위를 제한하고 사망 여부를 확인합니다.

        동작 흐름:
        1. max(0, min(value, max_hp)) 로 값을 0~max_hp 범위 안에 클램핑
           → HP가 음수가 되거나 최대치를 초과하는 일이 없음
        2. 클램핑된 HP가 0이고 AI가 아직 살아있으면 die()를 호출해 사망 처리

        예) target.fighter.hp -= 10 처럼 외부에서 HP를 깎으면 이 setter가 실행됨.
        """
        self._hp = max(0, min(value, self.max_hp))

        # HP가 0이 되고 AI가 살아있으면 → 사망 처리
        if self._hp == 0 and self.parent.ai:
            self.die()

    def die(self) -> None:
        """엔티티를 사망 상태로 전환합니다.

        동작 흐름 (플레이어):
        1. 사망 메시지를 빨간색으로 설정
        2. 이벤트 핸들러를 GameOverEventHandler로 교체 → 방향키 등 입력이 차단됨

        동작 흐름 (몬스터):
        1. 처치 메시지를 주황색으로 설정

        공통 처리:
        - char를 '%'(시체 기호)로, color를 빨간색으로 변경
        - blocks_movement = False → 시체 위로 걸어다닐 수 있게 됨
        - ai = None → is_alive가 False가 되어 더 이상 행동하지 않음
        - name에 "~ 의 유해" 추가
        - render_order를 CORPSE로 낮춰 아이템/캐릭터보다 아래에 그려짐
        - 사망 메시지를 메시지 로그에 추가
        """
        if self.engine.player is self.parent:
            # death_message = "당신은 죽었습니다."
            death_message = "You died!"
            death_message_color = color.player_die
        else:
            # death_message = f"{self.parent.name}을(를) 처치했습니다!"
            death_message = f"{self.parent.name} is dead!"
            death_message_color = color.enemy_die

        # 사망한 엔티티를 시체로 변환
        self.parent.char = "%"                                       # 시체 기호
        self.parent.color = (191, 0, 0)                             # 빨간색
        self.parent.blocks_movement = False                          # 시체 위로 이동 가능
        self.parent.ai = None                                        # AI 제거 (더 이상 행동 안 함)
        # self.parent.name = f"{self.parent.name} ~ 의 유해"
        self.parent.name = f"remains of {self.parent.name}"         # 이름을 "remains of ~"로 변경
        self.parent.render_order = RenderOrder.CORPSE        # 렌더 우선순위를 시체로 낮춤

        self.engine.message_log.add_message(death_message, death_message_color)

    def heal(self, amount: int) -> int:
        """HP를 amount만큼 회복하고, 실제로 회복된 양을 반환합니다.

        동작 흐름:
        1. 이미 HP가 최대치면 0을 반환 (회복 불가 → Impossible 예외는 호출자에서 처리)
        2. 회복 후 HP가 max_hp를 초과하면 max_hp로 제한
        3. 실제 회복량(= 회복 후 HP - 회복 전 HP)을 계산해 반환
           → 호출자(HealingConsumable)가 메시지에 실제 회복량을 표시하는 데 사용
        """
        if self.hp == self.max_hp:
            return 0

        new_hp_value = self.hp + amount

        if new_hp_value > self.max_hp:
            new_hp_value = self.max_hp

        amount_recovered = new_hp_value - self.hp

        self.hp = new_hp_value  # hp setter를 통해 설정 (클램핑 + 사망 체크 자동 적용)

        return amount_recovered

    def take_damage(self, amount: int) -> None:
        """HP를 amount만큼 직접 감소시킵니다.

        hp setter를 통해 감소하므로 자동으로 클램핑과 사망 처리가 적용됨.
        파이어볼, 번개 스크롤처럼 방어력을 무시하는 마법 피해에 사용.
        일반 근접 공격은 MeleeAction에서 직접 hp -= damage 로 처리.
        """
        self.hp -= amount
