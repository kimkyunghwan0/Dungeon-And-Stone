import copy
import tcod

import entity_factories
from engine import Engine
from procgen import generate_dungeon
from input_handlers import EventHandler

def main() -> None:
    # 화면 크기 설정 (픽셀이 아닌 타일 단위)
    screen_width = 80
    screen_height = 50

    # 맵 크기 설정 (화면보다 작게 — 나머지 공간은 UI용)
    map_width = 80
    map_height = 45

    # 방 크기 및 개수 설정
    room_max_size = 10      # 방 하나의 최대 크기
    room_min_size = 6       # 방 하나의 최소 크기
    max_rooms = 30          # 던전 내 최대 방 개수

    max_monsters_per_room = 2  # 방 하나에 등장할 수 있는 최대 몬스터 수

    # 글꼴(타일셋) 지정. 32열 8행짜리 타일 이미지
    tileset = tcod.tileset.load_tilesheet(
        "dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    event_handler = EventHandler()  # 키 입력 이벤트 처리기 생성

    # entity_factories의 player 원본을 복사해 독립적인 플레이어 인스턴스 생성
    player = copy.deepcopy(entity_factories.player)

    # 던전 맵 생성 (방 배치, 복도 연결, 몬스터 배치 포함)
    game_map = generate_dungeon(
        max_rooms=max_rooms,
        room_min_size=room_min_size,
        room_max_size=room_max_size,
        map_width=map_width,
        map_height=map_height,
        max_monsters_per_room=max_monsters_per_room,
        player=player
    )

    # 엔진 초기화 — 이벤트 처리기, 맵, 플레이어를 연결
    engine = Engine(event_handler=event_handler, game_map=game_map, player=player)

    # tcod 터미널 창 생성
    with tcod.context.new_terminal(
        screen_width,
        screen_height,
        tileset=tileset,
        title="Dungeon & Stone",  # 창 제목
        vsync=True,               # 수직동기화 (화면 찢김 방지)
    ) as context:
        # 콘솔 생성. order="F"로 설정 시 배열 인덱스가 [y,x] 대신 [x,y]로 동작
        root_console = tcod.Console(screen_width, screen_height, order="F")

        # 메인 게임 루프 — 렌더링 → 이벤트 대기 → 처리 순으로 반복
        while True:
            engine.render(console=root_console, context=context)  # 화면 그리기
            events = tcod.event.wait()                            # 키 입력 대기
            engine.handle_events(events)                          # 입력 처리

# __name__ 확인으로 이 파일이 직접 실행될 때만 main() 호출 (import 시에는 실행 안 됨)
if __name__ == "__main__":
    main()
