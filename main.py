#tcod == 로그라이크 게임용으로 특화된 pygame 라이브러리
import tcod

from actions import EscapeAction, MovementAction
from input_handlers import EventHandler

def main() -> None:
    # 화면 크기 설정
    screen_width = 80
    screen_height = 50
    # 플레이어 좌표 설정
    player_x = int(screen_width / 2)
    player_y = int(screen_height / 2)

    # 글꼴 지정. 후에 json 파일에 선언 예정
    tileset = tcod.tileset.load_tilesheet(
        "dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    event_handler = EventHandler()

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
            # 시작좌표, 표시
            root_console.print(x=player_x, y=player_y, string="@")

            # 실제 화면에 출력
            context.present(root_console)
            
            # 기존 콘솔 삭제... 없으면 움직일떄마다 흔적남음.
            root_console.clear()
            
            # 사용자 입력 대기 이벤트
            for event in tcod.event.wait():
                # 입력된 키 확인
                action = event_handler.dispatch(event)

                if action is None:
                    continue
                # action == 좌표이동(dx,dy)
                if isinstance(action, MovementAction):
                    player_x += action.dx
                    player_y += action.dy
                # action == 창 종료(Ecs)
                elif isinstance(action, EscapeAction):
                    raise SystemExit()
# __name을 사용하는 이유 : 시작점 구분.
if __name__ == "__main__":
    main()