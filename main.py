import copy
import tcod

import color
import entity_factories
from engine import Engine
from procgen import generate_dungeon

def main() -> None:
    # 화면 크기 설정 (픽셀이 아닌 타일 단위)
    screen_width = 80
    screen_height = 50

    # 맵 크기 설정 (화면보다 작게 — 나머지 공간은 UI용)
    map_width = 80
    map_height = 43

    # 방 크기 및 개수 설정
    room_max_size = 10      # 방 하나의 최대 크기
    room_min_size = 6       # 방 하나의 최소 크기
    max_rooms = 30          # 던전 내 최대 방 개수

    max_monsters_per_room = 2  # 방 하나에 등장할 수 있는 최대 몬스터 수

    # 글꼴(타일셋) 지정. TTF 폰트를 사용해 한글 유니코드 출력 지원
    # dejavu10x10_gs_tc.png(ASCII 전용 비트맵)는 한글을 표시할 수 없어 교체
    # tile_width/tile_height: 타일 한 칸의 픽셀 크기 (클수록 글자가 커짐)
    tileset = tcod.tileset.load_truetype_font(
        "C:/Windows/Fonts/malgun.ttf", tile_width=16, tile_height=16
    )

    # entity_factories의 player 원본을 복사해 독립적인 플레이어 인스턴스 생성
    player = copy.deepcopy(entity_factories.player)

    engine = Engine(player=player)

    # 던전 맵 생성 (방 배치, 복도 연결, 몬스터 배치 포함)
    engine.game_map = generate_dungeon(
        max_rooms=max_rooms,
        room_min_size=room_min_size,
        room_max_size=room_max_size,
        map_width=map_width,
        map_height=map_height,
        max_monsters_per_room=max_monsters_per_room,
        engine=engine,
    )

    engine.update_fov()

    # 최초 실행 메시지
    engine.message_log.add_message(
        "Hello and welcome, adventurer, to yet another dungeon!", color.welcome_text
    )

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
            root_console.clear()
            engine.event_handler.on_render(console=root_console)
            context.present(root_console)
            engine.event_handler.handle_events(context)         

# __name__ 확인으로 이 파일이 직접 실행될 때만 main() 호출 (import 시에는 실행 안 됨)
if __name__ == "__main__":
    main()
