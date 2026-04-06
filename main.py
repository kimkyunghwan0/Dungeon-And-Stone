import tcod

from engine import Engine
from entity import Entity
from game_map import GameMap
from input_handlers import EventHandler

def main() -> None:
    # 화면 크기 설정
    screen_width = 80
    screen_height = 50

    map_width = 80
    map_height = 45

    # 글꼴 지정. 후에 json 파일에 선언 예정
    tileset = tcod.tileset.load_tilesheet(
        "dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    event_handler = EventHandler()

    # 플레이어와 새로운 NPC를 초기화 및 저장
    player = Entity(int(screen_width / 2), int(screen_height / 2), "@", (255, 255, 255))
    npc = Entity(int(screen_width / 2 - 5), int(screen_height / 2), "@", (255, 255, 0))
    entities = {npc, player}

    game_map = GameMap(map_width, map_height)

    engine = Engine(entities=entities, event_handler=event_handler, game_map=game_map, player=player)

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