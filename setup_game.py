# 새 게임 생성, 세이브 파일 로드, 메인 메뉴를 처리합니다.
from __future__ import annotations

import copy
import lzma
import pickle
import traceback

from typing import Optional

import tcod

import color
from engine import Engine
import entity_factories
from game_map import GameWorld
import input_handlers

# Load the background image and remove the alpha channel.
background_image = tcod.image.load("menu_background.png")[:, :, :3]


def new_game() -> Engine:
    """새 게임 세션을 Engine 인스턴스로 생성해 반환합니다."""
    # 맵 크기 설정 (화면보다 작게 — 나머지 공간은 UI용)
    map_width = 80
    map_height = 43

    # 방 크기 및 개수 설정
    room_max_size = 10      # 방 하나의 최대 크기
    room_min_size = 6       # 방 하나의 최소 크기
    max_rooms = 30          # 던전 내 최대 방 개수

    max_monsters_per_room = 2  # 방 하나에 등장할 수 있는 최대 몬스터 수
    max_items_per_room  = 2  # 방 하나에 존재할 수 있는 최대 아이템 수

    # entity_factories의 player 원본을 복사해 독립적인 플레이어 인스턴스 생성
    player = copy.deepcopy(entity_factories.player)

    engine = Engine(player=player)

    # 던전 맵 생성 (방 배치, 복도 연결, 몬스터 배치 포함)
    engine.game_world = GameWorld(
        engine=engine,
        max_rooms=max_rooms,
        room_min_size=room_min_size,
        room_max_size=room_max_size,
        map_width=map_width,
        map_height=map_height,
        max_monsters_per_room=max_monsters_per_room,
        max_items_per_room=max_items_per_room,
    )
    
    engine.game_world.generate_floor()
    engine.update_fov()

    # 최초 실행 메시지
    engine.message_log.add_message(
        "Hello and welcome, adventurer, to yet another dungeon!", color.welcome_text
    )
    return engine

def load_game(filename: str) -> Engine:
    """저장 파일에서 Engine 인스턴스를 불러와 반환합니다."""
    with open(filename, "rb") as f:
        engine = pickle.loads(lzma.decompress(f.read()))
    assert isinstance(engine, Engine)
    return engine

# 게임 시작 시에만 보임.
# 게임 시작 화면 — 새 게임(N), 이어하기(C), 종료(Q)를 선택할 수 있음
class MainMenu(input_handlers.BaseEventHandler):
    """메인 메뉴 렌더링과 입력을 처리합니다."""

    def on_render(self, console: tcod.Console) -> None:
        """배경 이미지 위에 메인 메뉴를 렌더링합니다."""
        console.draw_semigraphics(background_image, 0, 0)

        console.print(
            console.width // 2,
            console.height // 2 - 4,
            "TOMBS OF THE ANCIENT KINGS",
            fg=color.menu_title,
            alignment=tcod.CENTER,
        )
        console.print(
            console.width // 2,
            console.height - 2,
            "By (Your name here)",
            fg=color.menu_title,
            alignment=tcod.CENTER,
        )

        menu_width = 24
        for i, text in enumerate(
            ["[N] Play a new game", "[C] Continue last game", "[Q] Quit"]
        ):
            console.print(
                console.width // 2,
                console.height // 2 - 2 + i,
                text.ljust(menu_width),
                fg=color.menu_text,
                bg=color.black,
                alignment=tcod.CENTER,
                bg_blend=tcod.BKGND_ALPHA(64),
            )

    def ev_keydown(
        self, event: tcod.event.KeyDown
    ) -> Optional[input_handlers.BaseEventHandler]:
        # Q --> 종료
        if event.sym in (tcod.event.K_q, tcod.event.K_ESCAPE):
            raise SystemExit()
        # C --> 게임 로드
        elif event.sym == tcod.event.K_c:
            try:
                return input_handlers.MainGameEventHandler(load_game("savegame.sav"))
            except FileNotFoundError:
                return input_handlers.PopupMessage(self, "No saved game to load.")
            except Exception as exc:
                traceback.print_exc()  # Print to stderr.
                return input_handlers.PopupMessage(self, f"Failed to load save:\n{exc}")
        # N --> 새 게임
        elif event.sym == tcod.event.K_n:
            return input_handlers.MainGameEventHandler(new_game())

        return None