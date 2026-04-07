from typing import Iterable, Any

from tcod.context import Context
from tcod.console import Console
from tcod.map import compute_fov

from entity import Entity
from game_map import GameMap
from input_handlers import EventHandler

# 게임의 핵심 루프를 담당하는 클래스
# 이벤트 처리 → 행동 수행 → FOV 갱신 → 화면 렌더링 순서로 동작
class Engine:
    # event_handler : 키 입력 이벤트 처리기 , game_map : 타일/엔티티 정보를 담은 맵 , player : 플레이어 엔티티
    def __init__(self, event_handler: EventHandler, game_map: GameMap, player: Entity):
        self.event_handler = event_handler
        self.game_map = game_map
        self.player = player
        self.update_fov()  # 1) Engine 초기화 시 → 게임 시작 직후 시야 확보

    # 플레이어를 제외한 모든 엔티티(적)의 턴을 처리
    def handle_enemy_turns(self) -> None:
        for entity in self.game_map.entities - {self.player}:  # set 차집합으로 플레이어 제외
            print(f'The {entity.name} wonders when it will get to take a real turn.')

    # 매 프레임마다 발생한 이벤트(키 입력 등)를 순서대로 처리
    def handle_events(self, events: Iterable[Any]) -> None:
        for event in events:
            # 이벤트를 해당 액션으로 변환 (이동, 종료 등)
            action = self.event_handler.dispatch(event)

            if action is None:  # 처리할 액션이 없으면 다음 이벤트로 넘어감
                continue

            action.perform(self, self.player)  # 액션 실행 (이동, 공격 등)

            self.handle_enemy_turns()  # 플레이어 행동 후 적 턴 처리

            # 2) 플레이어가 행동할 때마다 → 이동/행동 후 시야 갱신
            self.update_fov()

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

        context.present(console)  # 콘솔 내용을 실제 화면에 출력

        console.clear()  # 다음 프레임을 위해 콘솔 초기화 (없으면 이전 프레임 흔적 남음)