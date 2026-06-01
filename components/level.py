from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor


class Level(BaseComponent):
    parent: Actor

    def __init__(
        self,
        current_level: int = 1, # 엔티티의 현재 레벨이며, 기본값은 1입니다.
        current_xp: int = 0, # 엔티티의 현재 경험치.
        level_up_base: int = 0, # 레벨업을 위한 기본 수치입니다. 플레이어를 생성할 때 200으로 설정하겠습니다.
        level_up_factor: int = 150,  # 엔티티의 현재 레벨에 곱할 숫자입니다.
        xp_given: int = 0, # 엔티티가 죽을 때 플레이어가 얻게 될 경험치입니다.
    ):
        self.current_level = current_level
        self.current_xp = current_xp
        self.level_up_base = level_up_base
        self.level_up_factor = level_up_factor
        self.xp_given = xp_given

    # 플레이어가 다음 레벨에 도달하기까지 필요한 경험치
    @property
    def experience_to_next_level(self) -> int:
        return self.level_up_base + self.current_level * self.level_up_factor

    # 플레이어의 레벨업 필요 여부를 판단
    @property
    def requires_level_up(self) -> bool:
        return self.current_xp > self.experience_to_next_level

    # 엔티티의 경험치 풀에 경험치를 추가
    def add_xp(self, xp: int) -> None:
        if xp == 0 or self.level_up_base == 0:
            return

        self.current_xp += xp

        self.engine.message_log.add_message(f"You gain {xp} experience points.")

        if self.requires_level_up:
            self.engine.message_log.add_message(
                f"You advance to level {self.current_level + 1}!"
            )

    # 경험치 증가
    def increase_level(self) -> None:
        self.current_xp -= self.experience_to_next_level

        self.current_level += 1

    def increase_max_hp(self, amount: int = 20) -> None:
        self.parent.fighter.max_hp += amount
        self.parent.fighter.hp += amount

        self.engine.message_log.add_message("Your health improves!")

        self.increase_level()

    def increase_power(self, amount: int = 1) -> None:
        self.parent.fighter.power += amount

        self.engine.message_log.add_message("You feel stronger!")

        self.increase_level()

    def increase_defense(self, amount: int = 1) -> None:
        self.parent.fighter.defense += amount

        self.engine.message_log.add_message("Your movements are getting swifter!")

        self.increase_level()