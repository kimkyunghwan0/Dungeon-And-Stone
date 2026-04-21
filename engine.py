from __future__ import annotations

import lzma
import pickle

from typing import TYPE_CHECKING

from tcod.console import Console
from tcod.map import compute_fov

import exceptions

from message_log import MessageLog
from render_functions import render_bar, render_names_at_mouse_location

if TYPE_CHECKING:
    from entity import Actor
    from game_map import GameMap

# 게임의 핵심 루프를 담당하는 클래스
# 이벤트 처리 → 행동 수행 → FOV 갱신 → 화면 렌더링 순서로 동작
class Engine:

    def __init__(self, player: Actor):
        """엔진을 초기화합니다.

        동작 흐름:
        - event_handler : 현재 게임 상태(일반 플레이/게임오버 등)에 맞는 핸들러를 교체하며 사용
        - message_log   : 전투 결과, 아이템 사용 등 게임 이벤트 메시지를 누적 저장
        - mouse_location: 마우스 커서가 가리키는 맵 타일 좌표 (엔티티 이름 표시에 사용)
        - player        : 플레이어 Actor 엔티티
        - game_map은 이 __init__ 이후 main.py에서 engine.game_map = ... 으로 직접 할당됨
        """
        self.message_log = MessageLog()
        self.mouse_location = (0, 0)
        self.player = player

    def handle_enemy_turns(self) -> None:
        """플레이어를 제외한 살아있는 모든 Actor(적)의 턴을 처리합니다.

        동작 흐름:
        1. game_map.actors(살아있는 전체 Actor 집합)에서 플레이어를 차집합으로 제외
        2. 각 적 엔티티에 ai가 있으면 ai.perform()을 호출해 행동 실행
           - HostileEnemy: 플레이어 추적 또는 공격
           - ConfusedEnemy: 무작위 방향으로 이동
        3. Impossible 예외(벽으로 이동 등)는 조용히 무시 (적 턴이 낭비되는 것으로 처리)

        set()을 사용하는 이유: 이터레이션 중 집합이 변경될 수 있어 복사본으로 순회.
        """
        for entity in set(self.game_map.actors) - {self.player}:  # set 차집합으로 플레이어 제외
            if entity.ai:
                try:
                    # 각 적의 AI 행동 실행 (추적, 공격, 대기 등)
                    entity.ai.perform()
                except exceptions.Impossible:
                    pass  # AI의 불가능한 행동은 무시 (예: 벽으로 이동 시도)

    def update_fov(self) -> None:
        """플레이어 위치를 기준으로 시야(FOV)를 갱신합니다.

        동작 흐름:
        1. tcod.map.compute_fov()로 tiles["transparent"] 배열과 플레이어 위치, 반경을 넘겨
           현재 볼 수 있는 타일을 계산해 game_map.visible 배열에 저장
        2. visible 타일을 explored에 OR 연산으로 합산
           → 한 번이라도 본 타일은 어둡게라도 계속 화면에 표시됨

        visible  : 현재 이 순간 플레이어 눈에 보이는 타일 (밝게 표시)
        explored : 지금까지 한 번이라도 본 타일 (어둡게 표시, 시야 밖이어도 유지)
        """
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],  # 투명도 정보. 2D numpy 배열. 0이면 벽(불투명), 1이면 빈 공간(투명)
            (self.player.x, self.player.y),      # 시야 원점 (플레이어 위치)
            radius=8,                            # 시야 반경
        )
        self.game_map.explored |= self.game_map.visible  # 한 번 본 타일은 explored 상태 유지

    def render(self, console: Console) -> None:
        """현재 프레임을 콘솔에 그립니다.

        동작 흐름:
        1. game_map.render() : 맵 타일(바닥/벽)과 그 위의 엔티티(적, 아이템 등)를 그림
        2. message_log.render() : 화면 하단 메시지 영역에 최근 전투/이벤트 메시지를 출력
        3. render_bar() : 화면 왼쪽 하단에 플레이어 HP 바를 그림
        4. render_names_at_mouse_location() : 마우스 커서 위치의 엔티티 이름을 표시

        이 메서드가 끝나면 main.py의 context.present()가 콘솔을 실제 화면에 출력.
        """
        self.game_map.render(console)  # 맵(타일 + 엔티티)을 콘솔에 그림

        self.message_log.render(console=console, x=21, y=45, width=40, height=5)  # 메시지 로그

        # 화면 하단(y=45)에 플레이어 HP 바 표시
        render_bar(
            console=console,
            current_value=self.player.fighter.hp,
            maximum_value=self.player.fighter.max_hp,
            total_width=20,
        )

        # 마우스가 올라간 타일의 엔티티 이름을 HP 바 오른쪽(y=44)에 표시
        render_names_at_mouse_location(console=console, x=21, y=44, engine=self)
    def save_as(self, filename: str) -> None:
        """Save this Engine instance as a compressed file."""
        save_data = lzma.compress(pickle.dumps(self))
        with open(filename, "wb") as f:
            f.write(save_data)