# 엔티티의 레벨과 경험치 시스템(XP 획득 → 레벨업 → 능력치 선택)을 관리합니다.
from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor


# 레벨·경험치 시스템을 담당하는 컴포넌트
# Actor에 붙어 경험치 획득 → 레벨업 판단 → 능력치 선택까지 한 흐름을 처리
class Level(BaseComponent):
    parent: Actor

    def __init__(
        self,
        current_level: int = 1,
        current_xp: int = 0,
        level_up_base: int = 0,
        level_up_factor: int = 150,
        xp_given: int = 0,
    ):
        """레벨 컴포넌트를 초기화합니다.

        매개변수:
        - current_level   : 현재 레벨 (기본값 1)
        - current_xp      : 누적 경험치
        - level_up_base   : 레벨업에 필요한 기본 경험치 (플레이어: 200, 몬스터: 0)
        - level_up_factor : 레벨당 추가 요구 경험치 곱수 (기본값 150)
                            필요 경험치 공식: level_up_base + current_level × level_up_factor
        - xp_given        : 이 엔티티 사망 시 플레이어가 획득하는 경험치
                            (오크: 35, 트롤: 100 / 플레이어·레벨업 없는 엔티티: 0)
        """
        self.current_level = current_level
        self.current_xp = current_xp
        self.level_up_base = level_up_base
        self.level_up_factor = level_up_factor
        self.xp_given = xp_given

    @property
    def experience_to_next_level(self) -> int:
        """다음 레벨에 도달하기 위해 필요한 총 경험치를 반환합니다.

        공식: level_up_base + current_level × level_up_factor
        예) 레벨 1 플레이어: 200 + 1×150 = 350
            레벨 2 플레이어: 200 + 2×150 = 500
        레벨이 오를수록 요구 경험치가 선형으로 증가해 난이도가 점차 높아짐.
        """
        return self.level_up_base + self.current_level * self.level_up_factor

    @property
    def requires_level_up(self) -> bool:
        """현재 경험치가 레벨업 기준치를 초과했는지 여부를 반환합니다.

        EventHandler.handle_events()에서 매 유효 액션 후 확인하여
        True이면 LevelUpEventHandler로 전환해 능력치 선택 화면을 띄움.
        level_up_base가 0인 몬스터는 항상 False → 레벨업 불가.
        """
        return self.current_xp > self.experience_to_next_level

    def add_xp(self, xp: int) -> None:
        """경험치를 current_xp에 추가하고 레벨업 여부를 메시지로 알립니다.

        동작 흐름:
        1. xp가 0이거나 level_up_base가 0이면(= 레벨업 불가 엔티티) 즉시 반환
        2. current_xp에 xp를 더함
        3. 경험치 획득 메시지 출력
        4. requires_level_up이 True면 레벨업 예고 메시지 추가 출력
           → 실제 능력치 선택은 LevelUpEventHandler에서 별도 처리

        Fighter.die()에서 적 사망 시 xp_given만큼 플레이어에게 호출됨.
        """
        if xp == 0 or self.level_up_base == 0:
            return

        self.current_xp += xp

        self.engine.message_log.add_message(f"You gain {xp} experience points.")

        if self.requires_level_up:
            self.engine.message_log.add_message(
                f"You advance to level {self.current_level + 1}!"
            )

    def increase_level(self) -> None:
        """레벨을 1 올리고 경험치를 레벨업 비용만큼 차감합니다.

        동작 흐름:
        1. current_xp에서 experience_to_next_level을 빼 초과 경험치를 유지
        2. current_level을 1 증가

        increase_max_hp / increase_power / increase_defense 공통 마무리 단계로 호출됨.
        """
        self.current_xp -= self.experience_to_next_level

        self.current_level += 1

    def increase_max_hp(self, amount: int = 20) -> None:
        """최대 HP와 현재 HP를 amount만큼 늘리고 레벨을 올립니다.

        LevelUpEventHandler에서 'a' 키 선택 시 호출됨 (Constitution 선택).
        max_hp와 현재 hp 둘 다 늘려 선택 즉시 체력이 꽉 차도록 함.
        """
        self.parent.fighter.max_hp += amount
        self.parent.fighter.hp += amount

        self.engine.message_log.add_message("Your health improves!")

        self.increase_level()

    def increase_power(self, amount: int = 1) -> None:
        """공격력(power)을 amount만큼 올리고 레벨을 올립니다.

        LevelUpEventHandler에서 'b' 키 선택 시 호출됨 (Strength 선택).
        """
        self.parent.fighter.power += amount

        self.engine.message_log.add_message("You feel stronger!")

        self.increase_level()

    def increase_defense(self, amount: int = 1) -> None:
        """방어력(defense)을 amount만큼 올리고 레벨을 올립니다.

        LevelUpEventHandler에서 'c' 키 선택 시 호출됨 (Agility 선택).
        """
        self.parent.fighter.defense += amount

        self.engine.message_log.add_message("Your movements are getting swifter!")

        self.increase_level()