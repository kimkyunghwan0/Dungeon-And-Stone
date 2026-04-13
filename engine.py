from __future__ import annotations

from typing import TYPE_CHECKING

from tcod.console import Console
from tcod.map import compute_fov

from message_log import MessageLog
from input_handlers import MainGameEventHandler
from render_functions import render_bar, render_names_at_mouse_location

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
        self.message_log = MessageLog()
        self.mouse_location = (0, 0)
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
    def render(self, console: Console) -> None:
        self.game_map.render(console)  # 맵(타일 + 엔티티)을 콘솔에 그림

        self.message_log.render(console=console, x=21, y=45, width=40, height=5) # 메시지 로그 

        # 화면 하단(y=47)에 플레이어 HP 표시
        render_bar(
            console=console,
            current_value=self.player.fighter.hp,
            maximum_value=self.player.fighter.max_hp,
            total_width=20,
        )

        # 마우스 호버
        render_names_at_mouse_location(console=console, x=21, y=44, engine=self)