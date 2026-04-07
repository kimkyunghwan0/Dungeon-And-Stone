from typing import Set, Iterable, Any

from tcod.context import Context
from tcod.console import Console
from tcod.map import compute_fov

from entity import Entity
from game_map import GameMap
from input_handlers import EventHandler

# 1) Engine 초기화 시 → 게임 시작 직후 시야 확보
class Engine:
    # set : 엔티티 집합(리스트지만 안에 중복값 불가능) , event_handler : main.py의 이벤트 처리 , game_map : 맵의 크기 , player : 엔티티 플레이어
    def __init__(self, entities: Set[Entity], event_handler: EventHandler, game_map: GameMap, player: Entity):
        self.entities = entities
        self.event_handler = event_handler
        self.game_map = game_map
        self.player = player
        self.update_fov()

    # 사용자 입력 대기 이벤트
    # 2) 플레이어가 행동할 때마다 → 이동할 때마다 시야 갱신
    def handle_events(self, events: Iterable[Any]) -> None:
        for event in events:
            # 입력된 키 확인
            action = self.event_handler.dispatch(event)

            if action is None:
                continue
            
            action.perform(self, self.player)
            
            # 3) 플레이어의 다음 동작 전에 FOV를 업데이트합니다
            self.update_fov()

    # 시야각
    def update_fov(self) -> None:
        """플레이어의 시점을 기준으로 보이는 영역을 다시 계산합니다."""
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],  # 투명도 정보. 2D numpy 배열. 0이면 벽(불투명), 1이면 빈 공간(투명)
            (self.player.x, self.player.y),      # 시야 원점 (플레이어 위치)
            radius=8,                            # 시야 반경
        )
        # 한 번 본 타일은 계속 explored 상태 유지 (어둡게라도 보임)
        # visible  → 지금 이 순간 플레이어 눈에 보이는 타일
        # explored → 지금까지 한 번이라도 본 적 있는 타일
        self.game_map.explored |= self.game_map.visible 


    # 화면 그리기
    def render(self, console: Console, context: Context) -> None:
        # GameMap의 렌더링 메서드를 호출
        self.game_map.render(console)
         # 시작좌표, 표시
        for entity in self.entities:
            # FOV 내에 있는 엔티티만 출력
            if self.game_map.visible[entity.x, entity.y]:
                console.print(entity.x, entity.y, entity.char, fg=entity.color)

        # 실제 화면에 출력
        context.present(console)

        # 기존 콘솔 삭제... 없으면 움직일떄마다 흔적남음.
        console.clear()