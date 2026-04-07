import copy
import tcod

import entity_factories
from engine import Engine
from procgen import generate_dungeon
from input_handlers import EventHandler

def main() -> None:
    # 화면 크기 설정
    screen_width = 80
    screen_height = 50

    # 맵 크기 설정
    map_width = 80
    map_height = 45

    # 방 최대 크기, 최소 크기, 최대 개수
    room_max_size = 10
    room_min_size = 6
    max_rooms = 30

    max_monsters_per_room = 2
    
    # 글꼴 지정. 후에 json 파일에 선언 예정
    tileset = tcod.tileset.load_tilesheet(
        "dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    event_handler = EventHandler()

    # 플레이어를 초기화 및 저장
    player = copy.deepcopy(entity_factories.player)

    game_map = generate_dungeon(
        max_rooms=max_rooms,
        room_min_size=room_min_size,
        room_max_size=room_max_size,
        map_width=map_width,
        map_height=map_height,
        max_monsters_per_room=max_monsters_per_room,
        player=player
    )

    engine = Engine(event_handler=event_handler, game_map=game_map, player=player)
    
    with tcod.context.new_terminal(
        screen_width,
        screen_height,
        tileset=tileset,
        title="Dungeon & Stone", # 제목
        vsync=True, # 수직동기화
    ) as context:
        # 콘솔 생성. 
        # order은 x와y변수의 순서를 변경. 기본은 [y,x]. order = "F" 일 시 [x,y]로 변경
        root_console = tcod.Console(screen_width, screen_height, order="F")
        while True:
            engine.render(console=root_console, context=context)
            events = tcod.event.wait()
            engine.handle_events(events)
# __name을 사용하는 이유 : 시작점 구분.
if __name__ == "__main__":
    main()