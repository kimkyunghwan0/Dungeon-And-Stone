# 변수에 None 값이 들어올 수 있으면 Optional을 사용한다. 즉, None이 들어 올 수도 아닐 수도 있을때 사용.
from typing import Optional

# tcod의 event 모듈만 사용
import tcod.event

from actions import Action, EscapeAction, MovementAction

# 이벤트 관리
class EventHandler(tcod.event.EventDispatch[Action]):
    # 프로그램창에서 X 클릭으로 종료
    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()
    # 키입력 이벤트
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        # 유효한 키가 눌리지 않은 경우 null을 반환
        action: Optional[Action] = None

        key = event.sym

        # 위 방향키
        if key == tcod.event.K_UP:
            action = MovementAction(dx=0, dy=-1)
        # 아래 방향키    
        elif key == tcod.event.K_DOWN:
            action = MovementAction(dx=0, dy=1)
        # 왼쪽 방향키    
        elif key == tcod.event.K_LEFT:
            action = MovementAction(dx=-1, dy=0)
        # 오른쪽 방향키    
        elif key == tcod.event.K_RIGHT:
            action = MovementAction(dx=1, dy=0)
        # Ecs키
        elif key == tcod.event.K_ESCAPE:
            action = EscapeAction()

        # No valid key was pressed
        return action