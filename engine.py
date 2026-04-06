from typing import Set, Iterable, Any

from tcod.context import Context
from tcod.console import Console

from entity import Entity
from game_map import GameMap
from input_handlers import EventHandler


class Engine:
    # set : 엔티티 집합(리스트지만 안에 중복값 불가능) , event_handler : main.py의 이벤트 처리 , game_map : 맵의 크기 , player : 엔티티 플레이어
    def __init__(self, entities: Set[Entity], event_handler: EventHandler, game_map: GameMap, player: Entity):
        self.entities = entities
        self.event_handler = event_handler
        self.game_map = game_map
        self.player = player

    # 사용자 입력 대기 이벤트
    def handle_events(self, events: Iterable[Any]) -> None:
        for event in events:
            # 입력된 키 확인
            action = self.event_handler.dispatch(event)

            if action is None:
                continue
            
            action.perform(self, self.player)

    # 화면 그리기
    def render(self, console: Console, context: Context) -> None:
        # GameMap의 렌더링 메서드를 호출
        self.game_map.render(console)
         # 시작좌표, 표시
        for entity in self.entities:
            console.print(entity.x, entity.y, entity.char, fg=entity.color)

        # 실제 화면에 출력
        context.present(console)

        # 기존 콘솔 삭제... 없으면 움직일떄마다 흔적남음.
        console.clear()