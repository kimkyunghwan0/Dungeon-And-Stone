from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent
from input_handlers import GameOverEventHandler
from render_order import RenderOrder

if TYPE_CHECKING:
    from entity import Actor

# 전투 관련 스탯(HP, 방어력, 공격력)을 담당하는 컴포넌트
# Entity에 직접 넣지 않고 분리한 이유: 나중에 아이템이나 버프로 스탯을 수정하기 쉬움
class Fighter(BaseComponent):
    entity: Actor

    # hp     : 최대 체력 (초기 HP이기도 함)
    # defense: 방어력 — 받는 데미지에서 차감됨 (damage = power - defense)
    # power  : 공격력 — 상대방 defense를 빼고 남은 값이 실제 데미지
    def __init__(self, hp: int, defense: int, power: int):
        self.max_hp = hp
        self._hp = hp      # 실제 HP는 _hp(프라이빗)로 관리, 외부에서는 hp 프로퍼티로 접근
        self.defense = defense
        self.power = power

    @property
    def hp(self) -> int:
        # 현재 HP 반환 (읽기 전용 접근)
        return self._hp

    @hp.setter
    def hp(self, value: int) -> None:
        # HP를 변경할 때 0 미만 또는 max_hp 초과가 되지 않도록 클램핑
        # max(0, min(value, max_hp)) → 항상 0 ~ max_hp 범위 안에 유지
        self._hp = max(0, min(value, self.max_hp))

        # HP가 0이 되고 AI가 살아있으면 → 사망 처리
        if self._hp == 0 and self.entity.ai:
            self.die()

    def die(self) -> None:
        # 플레이어가 죽었을 때
        if self.engine.player is self.entity:
            death_message = "당신은 죽었습니다."
            # 이벤트 핸들러를 GameOver 상태로 전환 (방향키 등 일반 입력 차단)
            self.engine.event_handler = GameOverEventHandler(self.engine)
        # 몬스터가 죽었을 때
        else:
            death_message = f"{self.entity.name}을(를) 처치했습니다!"

        # 사망한 엔티티를 시체로 변환
        self.entity.char = "%"                              # 시체 기호
        self.entity.color = (191, 0, 0)                    # 빨간색
        self.entity.blocks_movement = False                 # 시체 위로 이동 가능
        self.entity.ai = None                              # AI 제거 (더 이상 행동 안 함)
        self.entity.name = f"{self.entity.name} ~ 의 유해" # 이름을 "~의 유해"로 변경
        self.entity.render_order = RenderOrder.CORPSE       # 렌더 우선순위를 시체로 낮춤

        print(death_message)