from __future__ import annotations

from typing import TYPE_CHECKING

from tcod.context import Context
from tcod.console import Console
from tcod.map import compute_fov

from input_handlers import MainGameEventHandler

if TYPE_CHECKING:
    from entity import Actor
    from game_map import GameMap
    from input_handlers import EventHandler
# 게임의 핵심 루프를 담당하는 클래스
# 이벤트 처리 → 행동 수행 → FOV 갱신 → 화면 렌더링 순서로 동작
class Engine:
    
    # player : 플레이어 Actor 엔티티
    # game_map은 __init__ 이후 main.py에서 engine.game_map = ... 으로 직접 할당됨
    def __init__(self, player: Actor):
        self.event_handler: EventHandler = MainGameEventHandler(self)  # 초기 상태는 일반 플레이
        self.player = player

    # 플레이어를 제외한 살아있는 모든 Actor(적)의 턴을 처리
    def handle_enemy_turns(self) -> None:
        for entity in set(self.game_map.actors) - {self.player}:  # set 차집합으로 플레이어 제외
            if entity.ai:
                entity.ai.perform()  # 각 적의 AI 행동 실행 (추적, 공격, 대기 등)
    # 플레이어 위치를 기준으로 시야(FOV)를 갱신
    def update_fov(self) -> None:
        """플레이어의 시점을 기준으로 보이는 영역을 다시 계산합니다."""
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],  # 투명도 정보. 2D numpy 배열. 0이면 벽(불투명), 1이면 빈 공간(투명)
            (self.player.x, self.player.y),      # 시야 원점 (플레이어 위치)
            radius=8,                            # 시야 반경
        )
        # visible  → 지금 이 순간 플레이어 눈에 보이는 타일
        # explored → 지금까지 한 번이라도 본 적 있는 타일 (어둡게라도 계속 표시)
        self.game_map.explored |= self.game_map.visible  # 한 번 본 타일은 explored 상태 유지

    # 현재 프레임을 화면에 그림
    def render(self, console: Console, context: Context) -> None:
        self.game_map.render(console)  # 맵(타일 + 엔티티)을 콘솔에 그림

        # 화면 하단(y=47)에 플레이어 HP 표시
        console.print(
            x=1,
            y=47,
            string=f"HP: {self.player.fighter.hp}/{self.player.fighter.max_hp}",
        )

        context.present(console)  # 콘솔 내용을 실제 화면에 출력

        console.clear()  # 다음 프레임을 위해 콘솔 초기화 (없으면 이전 프레임 흔적 남음)