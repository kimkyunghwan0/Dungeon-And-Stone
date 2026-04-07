from __future__ import annotations

# 반환값이 None일 수도 있는 경우 Optional을 사용
from typing import Optional, TYPE_CHECKING

import tcod.event

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
# Engine.event_handler에 현재 상태에 맞는 핸들러 인스턴스를 교체해서 사용
class EventHandler(tcod.event.EventDispatch[Action]):

    def __init__(self, engine: Engine):
        self.engine = engine  # 엔진 참조 (플레이어, 맵 등에 접근하기 위해)

    def handle_events(self) -> None:
        raise NotImplementedError()  # 하위 클래스에서 구현

    # 프로그램 창 X 버튼 클릭 시 즉시 종료
    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()


# ── 일반 플레이 상태 핸들러 ───────────────────────────────────────────────
class MainGameEventHandler(EventHandler):

    def handle_events(self) -> None:
        # tcod.event.wait()로 이벤트가 올 때까지 대기 후 처리
        for event in tcod.event.wait():
            action = self.dispatch(event)  # 이벤트 → 액션 변환

            if action is None:
                continue  # 매핑된 키가 없으면 무시

            action.perform()               # 액션 실행 (이동, 공격 등)

            self.engine.handle_enemy_turns()  # 플레이어 행동 후 모든 적 턴 처리
            self.engine.update_fov()          # 적 이동 후 시야 재계산

    # 눌린 키를 해당 Action으로 변환
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        action: Optional[Action] = None

        key = event.sym       # 눌린 키의 심볼 코드
        player = self.engine.player

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)  # 이동 또는 공격 자동 판단
        elif key in WAIT_KEYS:
            action = WaitAction(player)           # 한 턴 대기
        elif key == tcod.event.K_ESCAPE:
            action = EscapeAction(player)         # 게임 종료

        # 매핑되지 않은 키는 None 반환 (아무 동작 없음)
        return action


# ── 게임오버 상태 핸들러 ──────────────────────────────────────────────────
# 플레이어 사망 후 활성화. Esc 키로 종료만 가능하고 이동/공격 불가
class GameOverEventHandler(EventHandler):

    def handle_events(self) -> None:
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

        return action