import traceback

import tcod

import color
import exceptions
import input_handlers
import setup_game

def save_game(handler: input_handlers.BaseEventHandler, filename: str) -> None:
    """If the current event handler has an active Engine then save it."""
    if isinstance(handler, input_handlers.EventHandler):
        handler.engine.save_as(filename)
        print("Game saved.")

def main() -> None:
    # 화면 크기 설정 (픽셀이 아닌 타일 단위)
    screen_width = 80
    screen_height = 50

    # 글꼴(타일셋) 지정. TTF 폰트를 사용해 한글 유니코드 출력 지원
    # dejavu10x10_gs_tc.png(ASCII 전용 비트맵)는 한글을 표시할 수 없어 교체
    # tile_width/tile_height: 타일 한 칸의 픽셀 크기 (클수록 글자가 커짐)
    tileset = tcod.tileset.load_tilesheet(
        "dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    handler: input_handlers.BaseEventHandler = setup_game.MainMenu()

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
        try:
            while True:
                root_console.clear()
                handler.on_render(console=root_console)
                context.present(root_console)
                # 이벤트 대기 try catch
                try:
                    for event in tcod.event.wait():
                        context.convert_event(event)
                        handler = handler.handle_events(event)
                except Exception:  # 게임 중 발생한 예외를 처리
                    traceback.print_exc()  # 오류 내용을 stderr에 출력
                    # 동시에 게임 메시지 로그에도 오류를 표시해 플레이어가 볼 수 있도록 함
                    if isinstance(handler, input_handlers.EventHandler):
                        handler.engine.message_log.add_message(
                            traceback.format_exc(), color.error
                        )
        except exceptions.QuitWithoutSaving: # 강제종료
            raise
        except SystemExit:  # 저장 후 종료
            save_game(handler, "savegame.sav")
            raise
        except BaseException:  # 예외 사항
            save_game(handler, "savegame.sav")
            raise

# __name__ 확인으로 이 파일이 직접 실행될 때만 main() 호출 (import 시에는 실행 안 됨)
if __name__ == "__main__":
    main()
