from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import tcod

from actions import Action, BumpAction, EscapeAction, WaitAction

if TYPE_CHECKING:
    from engine import Engine


# ── 키 → (dx, dy) 매핑 딕셔너리 ──────────────────────────────────────────
# 방향키, 숫자패드, Vi 키 세 가지 방식 모두 지원
MOVE_KEYS = {
    # 방향키
    tcod.event.K_UP:       (0, -1),   # 위
    tcod.event.K_DOWN:     (0,  1),   # 아래
    tcod.event.K_LEFT:     (-1, 0),   # 왼쪽
    tcod.event.K_RIGHT:    (1,  0),   # 오른쪽
    tcod.event.K_HOME:     (-1, -1),  # 좌상단 대각선
    tcod.event.K_END:      (-1,  1),  # 좌하단 대각선
    tcod.event.K_PAGEUP:   (1, -1),   # 우상단 대각선
    tcod.event.K_PAGEDOWN: (1,  1),   # 우하단 대각선
    # 숫자패드 (5 제외 — 5는 대기 키)
    tcod.event.K_KP_1: (-1,  1),
    tcod.event.K_KP_2: (0,   1),
    tcod.event.K_KP_3: (1,   1),
    tcod.event.K_KP_4: (-1,  0),
    tcod.event.K_KP_6: (1,   0),
    tcod.event.K_KP_7: (-1, -1),
    tcod.event.K_KP_8: (0,  -1),
    tcod.event.K_KP_9: (1,  -1),
    # Vi 키 (로그라이크 전통 키 배열)
    tcod.event.K_h: (-1,  0),  # 왼쪽
    tcod.event.K_j: (0,   1),  # 아래
    tcod.event.K_k: (0,  -1),  # 위
    tcod.event.K_l: (1,   0),  # 오른쪽
    tcod.event.K_y: (-1, -1),  # 좌상단
    tcod.event.K_u: (1,  -1),  # 우상단
    tcod.event.K_b: (-1,  1),  # 좌하단
    tcod.event.K_n: (1,   1),  # 우하단
}

# 제자리 대기 키 (이동 없이 한 턴 소비)
WAIT_KEYS = {
    tcod.event.K_PERIOD,  # '.' 키
    tcod.event.K_KP_5,    # 숫자패드 5
    tcod.event.K_CLEAR,   # Clear 키
}


# ── 이벤트 핸들러 기본 클래스 ─────────────────────────────────────────────
# 게임 상태(일반 플레이, 게임오버 등)에 따라 다른 핸들러를 사용
# Engine.event_handler에 현재 상태에 맞는 핸들러 인스턴스를 교체해서 상태 전환
class EventHandler(tcod.event.EventDispatch[Action]):
    def __init__(self, engine: Engine):
        self.engine = engine  # 엔진 참조 (플레이어, 맵 등에 접근하기 위해)

    def handle_events(self, context: tcod.context.Context) -> None:
        for event in tcod.event.wait():
            # 이벤트에 마우스 좌표 정보 등을 추가 변환
            context.convert_event(event)
            # 이벤트 타입에 맞는 함수 호출 (ev_keydown, ev_quit 등)
            self.dispatch(event)

    # 마우스 이동 시 현재 타일 좌표를 엔진에 저장 (엔티티 이름 표시에 사용)
    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = event.tile.x, event.tile.y

    # 프로그램 창 X 버튼 클릭 시 즉시 종료
    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()

    # 현재 게임 화면을 콘솔에 그림 (서브클래스에서 오버라이드 가능)
    def on_render(self, console: tcod.Console) -> None:
        self.engine.render(console)


# ── 일반 플레이 상태 핸들러 ───────────────────────────────────────────────
class MainGameEventHandler(EventHandler):
    def handle_events(self, context: tcod.context.Context) -> None:
        # tcod.event.wait()로 이벤트가 올 때까지 대기 후 처리
        for event in tcod.event.wait():
            context.convert_event(event)

            action = self.dispatch(event)  # 이벤트 → 액션 변환

            if action is None:
                continue  # 매핑된 키가 없으면 무시

            action.perform()               # 액션 실행 (이동, 공격 등)

            self.engine.handle_enemy_turns()  # 플레이어 행동 후 모든 적 턴 처리

            self.engine.update_fov()  # 플레이어 다음 행동 전에 시야를 갱신

    # 눌린 키를 해당 Action으로 변환해 반환
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        action: Optional[Action] = None

        key = event.sym  # 눌린 키의 심볼 코드

        player = self.engine.player

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)  # 이동 또는 공격 자동 판단
        elif key in WAIT_KEYS:
            action = WaitAction(player)  # 한 턴 대기

        elif key == tcod.event.K_ESCAPE:
            action = EscapeAction(player)  # 게임 종료
        elif key == tcod.event.K_v:
            # 'v' 키 → 메시지 이력 뷰어 열기
            self.engine.event_handler = HistoryViewer(self.engine)

        # 매핑되지 않은 키는 None 반환 (아무 동작 없음)
        return action


# ── 게임오버 상태 핸들러 ──────────────────────────────────────────────────
# 플레이어 사망 후 활성화. Esc 키로 종료만 가능하고 이동/공격 불가
class GameOverEventHandler(EventHandler):
    def handle_events(self, context: tcod.context.Context) -> None:
        for event in tcod.event.wait():
            action = self.dispatch(event)

            if action is None:
                continue

            action.perform()

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        action: Optional[Action] = None

        key = event.sym

        # 게임오버 상태에서는 Esc 키로만 종료 가능
        if key == tcod.event.K_ESCAPE:
            action = EscapeAction(self.engine.player)

        # 매핑되지 않은 키는 None 반환
        return action


# 메시지 이력 뷰어에서 스크롤에 사용하는 키 → 이동량 매핑
# 양수면 아래(최신), 음수면 위(오래된) 방향
CURSOR_Y_KEYS = {
    tcod.event.K_UP:       -1,   # 위로 1칸
    tcod.event.K_DOWN:      1,   # 아래로 1칸
    tcod.event.K_PAGEUP:  -10,   # 위로 10칸
    tcod.event.K_PAGEDOWN: 10,   # 아래로 10칸
}


# ── 메시지 이력 뷰어 ──────────────────────────────────────────────────────
# 'v' 키를 누르면 활성화. 지금까지의 메시지 기록을 큰 창에서 스크롤하며 확인 가능
# cursor : 현재 보고 있는 메시지 인덱스 (0 = 가장 오래된, log_length-1 = 최신)
class HistoryViewer(EventHandler):
    """메시지 기록을 별도 창으로 표시하고 스크롤로 탐색할 수 있는 핸들러."""

    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1  # 초기에는 가장 최신 메시지를 표시

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)  # 배경으로 메인 게임 화면을 먼저 그림

        # 메인 콘솔보다 작은 별도 콘솔 생성 (상하좌우 3칸씩 여백)
        log_console = tcod.Console(console.width - 6, console.height - 6)

        # 테두리 프레임 그리기
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        # 상단 중앙에 제목 배너 출력
        log_console.print_box(
            0, 0, log_console.width, 1, "┤Message history├", alignment=tcod.CENTER
        )

        # cursor 위치까지의 메시지만 잘라서 렌더링 (스크롤 위치 반영)
        self.engine.message_log.render_messages(
            log_console,
            1,
            1,
            log_console.width - 2,
            log_console.height - 2,
            self.engine.message_log.messages[: self.cursor + 1],
        )
        # 완성된 뷰어 콘솔을 메인 콘솔 (3,3) 위치에 합성
        log_console.blit(console, 3, 3)

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        # 경계에서 반대편으로 순환되도록 자연스러운 스크롤 처리
        if event.sym in CURSOR_Y_KEYS:
            adjust = CURSOR_Y_KEYS[event.sym]
            if adjust < 0 and self.cursor == 0:
                # 맨 위(가장 오래된)에서 더 위로 → 맨 아래(최신)로 순환
                self.cursor = self.log_length - 1
            elif adjust > 0 and self.cursor == self.log_length - 1:
                # 맨 아래(최신)에서 더 아래로 → 맨 위(가장 오래된)로 순환
                self.cursor = 0
            else:
                # 경계를 벗어나지 않도록 클램핑하며 cursor 이동
                self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1))
        elif event.sym == tcod.event.K_HOME:
            self.cursor = 0  # 가장 오래된 메시지로 이동
        elif event.sym == tcod.event.K_END:
            self.cursor = self.log_length - 1  # 가장 최신 메시지로 이동
        else:  # 그 외 키 → 일반 플레이 상태로 복귀
            self.engine.event_handler = MainGameEventHandler(self.engine)