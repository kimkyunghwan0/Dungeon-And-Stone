from __future__ import annotations

import os

from typing import Callable, Optional, Tuple, TYPE_CHECKING, Union

import tcod
import actions

from actions import (
    Action,
    BumpAction,
    PickupAction,
    WaitAction
)

import color
import exceptions

if TYPE_CHECKING:
    from engine import Engine
    from entity import Item

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

CONFIRM_KEYS = {
    tcod.event.K_RETURN,
    tcod.event.K_KP_ENTER,
}

ActionOrHandler = Union[Action, "BaseEventHandler"]

""" 
    액션을 트리거하거나 활성 핸들러를 전환할 수 있는 이벤트 핸들러 반환 값입니다. 
    핸들러가 반환되면 향후 이벤트에 대한 활성 핸들러가 됩니다. 
    액션이 반환되면 시도되고, 유효하면 
    MainGameEventHandler가 활성 핸들러가 됩니다. 
"""


class BaseEventHandler(tcod.event.EventDispatch[ActionOrHandler]):
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """이벤트를 처리하고 다음 활성 이벤트 핸들러를 반환합니다."""
        state = self.dispatch(event)
        if isinstance(state, BaseEventHandler):
            return state
        assert not isinstance(state, Action), f"{self!r} can not handle actions."
        return self

    def on_render(self, console: tcod.Console) -> None:
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()

class PopupMessage(BaseEventHandler):
    """Display a popup text window."""

    def __init__(self, parent_handler: BaseEventHandler, text: str):
        self.parent = parent_handler
        self.text = text

    def on_render(self, console: tcod.Console) -> None:
        """Render the parent and dim the result, then print the message on top."""
        self.parent.on_render(console)
        console.tiles_rgb["fg"] //= 8
        console.tiles_rgb["bg"] //= 8

        console.print(
            console.width // 2,
            console.height // 2,
            self.text,
            fg=color.white,
            bg=color.black,
            alignment=tcod.CENTER,
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        """Any key returns to the parent handler."""
        return self.parent
    
# ── 이벤트 핸들러 기본 클래스 ─────────────────────────────────────────────
# 게임 상태(일반 플레이, 게임오버 등)에 따라 다른 핸들러를 사용
# Engine.event_handler에 현재 상태에 맞는 핸들러 인스턴스를 교체해서 상태 전환
class EventHandler(BaseEventHandler):
    def __init__(self, engine: Engine):
        self.engine = engine  # 엔진 참조 (플레이어, 맵 등에 접근하기 위해)

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle events for input handlers with an engine."""
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        if self.handle_action(action_or_state):
            # A valid action was performed.
            if not self.engine.player.is_alive:
                # The player was killed sometime during or after the action.
                return GameOverEventHandler(self.engine)
            return MainGameEventHandler(self.engine)  # Return to the main handler.
        return self

    def handle_action(self, action: Optional[Action]) -> bool:
        """이벤트 메서드에서 반환된 액션을 처리합니다.

        액션이 성공적으로 수행되어 한 턴이 진행됐으면 True를 반환합니다.
        """
        if action is None:
            return False

        try:
            action.perform()
        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], color.impossible)
            return False  # 불가능한 액션 예외 시 적의 턴을 건너뜀

        self.engine.handle_enemy_turns()

        self.engine.update_fov()
        return True
    
    # 마우스 이동 시 현재 타일 좌표를 엔진에 저장 (엔티티 이름 표시에 사용)
    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = event.tile.x, event.tile.y

    # 현재 게임 화면을 콘솔에 그림 (서브클래스에서 오버라이드 가능)
    def on_render(self, console: tcod.Console) -> None:
        self.engine.render(console)

class AskUserEventHandler(EventHandler):
    """특별한 입력(타겟 선택, 인벤토리 등)이 필요한 액션 전용 이벤트 핸들러 기반 클래스."""

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """기본적으로 어떤 키를 눌러도 이 핸들러를 종료합니다."""
        if event.sym in {  # Shift, Ctrl, Alt 등 수정자 키는 무시
            tcod.event.K_LSHIFT,
            tcod.event.K_RSHIFT,
            tcod.event.K_LCTRL,
            tcod.event.K_RCTRL,
            tcod.event.K_LALT,
            tcod.event.K_RALT,
        }:
            return None
        return self.on_exit()

    def ev_mousebuttondown(
        self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """기본적으로 마우스 클릭 시 이 핸들러를 종료합니다."""
        return self.on_exit()

    def on_exit(self) -> Optional[ActionOrHandler]:
        """사용자가 액션을 취소하거나 나가려 할 때 호출됩니다.

        기본적으로 일반 게임 이벤트 핸들러로 복귀합니다.
        """
        return MainGameEventHandler(self.engine)
    
class InventoryEventHandler(AskUserEventHandler):
    """인벤토리 아이템 선택 화면을 처리하는 핸들러 기반 클래스.

    실제 선택 후 동작(사용/버리기 등)은 서브클래스에서 결정합니다.
    """

    TITLE = "<missing title>"

    def on_render(self, console: tcod.Console) -> None:
        """인벤토리 메뉴를 렌더링합니다.
        플레이어 위치에 따라 창 위치가 달라져 플레이어 캐릭터를 가리지 않도록 합니다.
        """
        super().on_render(console)
        number_of_items_in_inventory = len(self.engine.player.inventory.items)

        height = number_of_items_in_inventory + 2

        if height <= 3:
            height = 3

        if self.engine.player.x <= 30:
            x = 40
        else:
            x = 0

        y = 0

        width = len(self.TITLE) + 4

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        if number_of_items_in_inventory > 0:
            for i, item in enumerate(self.engine.player.inventory.items):
                item_key = chr(ord("a") + i)
                console.print(x + 1, y + i + 1, f"({item_key}) {item.name}")
        else:
            console.print(x + 1, y + 1, "(Empty)")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 26:
            try:
                selected_item = player.inventory.items[index]
            except IndexError:
                # self.engine.message_log.add_message("잘못된 선택입니다.", color.invalid)
                self.engine.message_log.add_message("Invalid entry.", color.invalid)
                return None
            return self.on_item_selected(selected_item)
        return super().ev_keydown(event)

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """유효한 아이템이 선택됐을 때 호출됩니다. 서브클래스에서 반드시 구현해야 합니다."""
        raise NotImplementedError()

# 아이템 사용
class InventoryActivateHandler(InventoryEventHandler):
    """인벤토리에서 아이템을 선택해 사용하는 핸들러."""

    # TITLE = "사용할 아이템 선택"
    TITLE = "Select an item to use"

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """선택된 아이템에 대한 사용 액션을 반환합니다."""
        return item.consumable.get_action(self.engine.player)

# 아이템 버리기
class InventoryDropHandler(InventoryEventHandler):
    """인벤토리에서 아이템을 선택해 버리는 핸들러."""

    # TITLE = "버릴 아이템 선택"
    TITLE = "Select an item to drop"

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """선택된 아이템을 버리는 액션을 반환합니다."""
        return actions.DropItem(self.engine.player, item)

class SelectIndexHandler(AskUserEventHandler):
    """맵 위의 특정 타일 좌표를 선택하도록 사용자에게 요청하는 핸들러."""

    def __init__(self, engine: Engine):
        """핸들러 생성 시 커서를 플레이어 위치로 초기화합니다."""
        super().__init__(engine)
        player = self.engine.player
        engine.mouse_location = player.x, player.y

    def on_render(self, console: tcod.Console) -> None:
        """커서가 위치한 타일을 반전색으로 강조 표시합니다."""
        super().on_render(console)
        x, y = self.engine.mouse_location
        console.tiles_rgb["bg"][x, y] = color.white
        console.tiles_rgb["fg"][x, y] = color.black

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """이동 키 또는 확인 키를 처리합니다."""
        key = event.sym
        if key in MOVE_KEYS:
            modifier = 1  # Shift/Ctrl/Alt를 함께 누르면 커서가 더 빠르게 이동
            if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
                modifier *= 5   # Shift: 5칸씩 이동
            if event.mod & (tcod.event.KMOD_LCTRL | tcod.event.KMOD_RCTRL):
                modifier *= 10  # Ctrl: 10칸씩 이동
            if event.mod & (tcod.event.KMOD_LALT | tcod.event.KMOD_RALT):
                modifier *= 20  # Alt: 20칸씩 이동

            x, y = self.engine.mouse_location
            dx, dy = MOVE_KEYS[key]
            x += dx * modifier
            y += dy * modifier
            # 커서가 맵 밖으로 나가지 않도록 클램핑
            x = max(0, min(x, self.engine.game_map.width - 1))
            y = max(0, min(y, self.engine.game_map.height - 1))
            self.engine.mouse_location = x, y
            return None
        elif key in CONFIRM_KEYS:
            return self.on_index_selected(*self.engine.mouse_location)
        return super().ev_keydown(event)

    def ev_mousebuttondown(
        self, event: tcod.event.MouseButtonDown
    ) -> Optional[ActionOrHandler]:
        """마우스 좌클릭으로 타일을 선택합니다."""
        if self.engine.game_map.in_bounds(*event.tile):
            if event.button == 1:
                return self.on_index_selected(*event.tile)
        return super().ev_mousebuttondown(event)

    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        """타일 좌표가 선택됐을 때 호출됩니다. 서브클래스에서 반드시 구현해야 합니다."""
        raise NotImplementedError()

class LookHandler(SelectIndexHandler):
    """키보드로 맵을 탐색(커서 이동)할 수 있는 핸들러. '/' 키로 진입합니다."""

    def on_index_selected(self, x: int, y: int) -> MainGameEventHandler:
        """타일 선택 시 일반 게임 핸들러로 복귀합니다."""
        return MainGameEventHandler(self.engine)

# 단일공격대상
class SingleRangedAttackHandler(SelectIndexHandler):
    """단일 적을 타겟으로 지정하는 핸들러. 선택된 적 한 명에게만 효과가 적용됩니다."""

    def __init__(
        self, engine: Engine, callback: Callable[[Tuple[int, int]], Optional[Action]]
    ):
        super().__init__(engine)

        self.callback = callback

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))

# 범위공격대상
class AreaRangedAttackHandler(SelectIndexHandler):
    """범위 타겟을 지정하는 핸들러. 지정한 반경 내의 모든 엔티티에게 효과가 적용됩니다."""

    def __init__(
        self,
        engine: Engine,
        radius: int,
        callback: Callable[[Tuple[int, int]], Optional[Action]],
    ):
        super().__init__(engine)

        self.radius = radius
        self.callback = callback

    def on_render(self, console: tcod.Console) -> None:
        """커서 아래 타일을 강조하고, 범위를 나타내는 사각형 프레임을 그립니다."""
        super().on_render(console)

        x, y = self.engine.mouse_location

        # 영향 받는 범위를 플레이어가 볼 수 있도록 타겟 주변에 사각형 프레임 표시
        console.draw_frame(
            x=x - self.radius - 1,
            y=y - self.radius - 1,
            width=self.radius ** 2,
            height=self.radius ** 2,
            fg=color.red,
            clear=False,
        )

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))

# ── 일반 플레이 상태 핸들러 ───────────────────────────────────────────────
class MainGameEventHandler(EventHandler):
    # 눌린 키를 해당 Action으로 변환해 반환
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        action: Optional[Action] = None

        key = event.sym  # 눌린 키의 심볼 코드

        player = self.engine.player

        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)  # 이동 또는 공격 자동 판단
        elif key in WAIT_KEYS:
            action = WaitAction(player)  # 한 턴 대기

        elif key == tcod.event.K_ESCAPE:
            raise SystemExit()  # 게임 종료
        elif key == tcod.event.K_v:
            # 'v' 키 → 메시지 이력 뷰어 열기
            return HistoryViewer(self.engine)

        elif key == tcod.event.K_g:
            # 'g' 키 -> 아이템 줍기
            action = PickupAction(player)

        # 'i' 키 -> 인벤토리
        elif key == tcod.event.K_i:
            return InventoryActivateHandler(self.engine)
        # 'd' 키 -> 버리기 드롭다운메뉴    
        elif key == tcod.event.K_d:
            return InventoryDropHandler(self.engine)
        # '/' 키 ->  지도확인
        elif key == tcod.event.K_SLASH:
            return LookHandler(self.engine)
        # 매핑되지 않은 키는 None 반환 (아무 동작 없음)
        return action


# ── 게임오버 상태 핸들러 ──────────────────────────────────────────────────
# 플레이어 사망 후 활성화. Esc 키로 종료만 가능하고 이동/공격 불가
class GameOverEventHandler(EventHandler):
    def on_quit(self) -> None:
        """Handle exiting out of a finished game."""
        if os.path.exists("savegame.sav"):
            os.remove("savegame.sav")  # Deletes the active save file.
        raise exceptions.QuitWithoutSaving()  # Avoid saving a finished game.

    def ev_quit(self, event: tcod.event.Quit) -> None:
        self.on_quit()

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[MainGameEventHandler]:
        if event.sym == tcod.event.K_ESCAPE:
            self.on_quit()


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
            return MainGameEventHandler(self.engine)
        return None