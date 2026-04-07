# 반환값이 None일 수도 있는 경우 Optional을 사용
from typing import Optional

# tcod의 event 모듈만 사용
import tcod.event

from actions import Action, BumpAction, EscapeAction

# 키 입력 이벤트를 받아 대응하는 Action 객체로 변환하는 클래스
class EventHandler(tcod.event.EventDispatch[Action]):
    # 프로그램창에서 X 클릭 시 종료
    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()

    # 키 입력 이벤트 — 눌린 키에 맞는 Action을 반환, 매핑 없는 키는 None 반환
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        action: Optional[Action] = None

        key = event.sym  # 눌린 키의 심볼(코드)

        # 방향키 → BumpAction (이동 또는 공격을 자동 판단)
        if key == tcod.event.K_UP:
            action = BumpAction(dx=0, dy=-1)   # 위
        elif key == tcod.event.K_DOWN:
            action = BumpAction(dx=0, dy=1)    # 아래
        elif key == tcod.event.K_LEFT:
            action = BumpAction(dx=-1, dy=0)   # 왼쪽
        elif key == tcod.event.K_RIGHT:
            action = BumpAction(dx=1, dy=0)    # 오른쪽
        # Esc 키 → 게임 종료
        elif key == tcod.event.K_ESCAPE:
            action = EscapeAction()

        # 위에 매핑되지 않은 키는 None 반환 (아무 동작 없음)
        return action