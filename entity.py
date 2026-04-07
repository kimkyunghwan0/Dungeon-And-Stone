from __future__ import annotations

import copy
from typing import Optional, Tuple, Type, TypeVar, TYPE_CHECKING

from render_order import RenderOrder

if TYPE_CHECKING:
    from components.ai import BaseAI
    from components.fighter import Fighter
    from game_map import GameMap

# Entity 하위 클래스도 spawn()에서 올바른 타입을 반환받기 위한 제네릭 타입 변수
# 예: Actor.spawn()이 Entity가 아닌 Actor 타입으로 반환되도록 보장
T = TypeVar("T", bound="Entity")

# 플레이어, 적, 아이템 등을 나타내는 일반적인 객체
class Entity:
    # 클래스 변수 선언 — __init__에서 gamemap이 제공되지 않을 수도 있으므로
    # 타입 힌트만 선언하고 실제 할당은 나중에 함 (gamemap 없이 생성 후 나중에 연결)
    gamemap: GameMap

    # x, y         : 맵 좌표
    # char         : 화면에 표시될 문자 (예: '@', 'o', 'T')
    # color        : 문자 색상 (RGB 튜플)
    # name         : 엔티티 이름
    # blocks_movement : True이면 다른 엔티티가 이 위치로 이동 불가
    # render_order : 렌더링 우선순위 (CORPSE < ITEM < ACTOR 순으로 위에 그려짐)
    def __init__(
        self,
        gamemap: Optional[GameMap] = None,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        blocks_movement: bool = False,
        render_order: RenderOrder = RenderOrder.CORPSE,
    ):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks_movement = blocks_movement
        self.render_order = render_order

        if gamemap:
            # gamemap이 제공된 경우 즉시 연결. 아니면 나중에 spawn()이나 place()로 연결
            self.gamemap = gamemap
            gamemap.entities.add(self)

    def spawn(self: T, gamemap: GameMap, x: int, y: int) -> T:
        """주어진 위치에 이 인스턴스의 복사본을 생성합니다."""
        clone = copy.deepcopy(self)  # 원본 엔티티를 깊은 복사 (독립적인 새 인스턴스)
        clone.x = x
        clone.y = y
        clone.gamemap = gamemap
        gamemap.entities.add(clone)  # 맵의 엔티티 집합에 추가
        return clone

    # 엔티티를 dx, dy만큼 이동 (현재 좌표에 더함)
    def move(self, dx: int, dy: int) -> None:
        self.x += dx
        self.y += dy

    def place(self, x: int, y: int, gamemap: Optional[GameMap] = None) -> None:
        """이 엔티티를 새 위치에 배치합니다. 맵을 이동할 때도 사용합니다."""
        self.x = x
        self.y = y
        if gamemap:
            if hasattr(self, "gamemap"):  # gamemap이 아직 초기화되지 않았을 수 있음
                self.gamemap.entities.remove(self)  # 기존 맵에서 제거
            self.gamemap = gamemap
            gamemap.entities.add(self)  # 새 맵에 추가


# 행동(AI)과 전투 능력(Fighter)을 가진 살아있는 캐릭터 (플레이어, 몬스터)
# Entity를 상속하며, blocks_movement=True와 render_order=ACTOR가 기본값
class Actor(Entity):
    # ai_cls  : 사용할 AI 클래스 타입 (예: HostileEnemy). 인스턴스가 아닌 클래스를 받음
    # fighter : 전투 스탯 컴포넌트 (HP, 공격력, 방어력)
    def __init__(
        self,
        *,  # 이후 파라미터는 모두 키워드 전용
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        ai_cls: Type[BaseAI],
        fighter: Fighter,
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=True,          # 살아있는 캐릭터는 항상 이동을 막음
            render_order=RenderOrder.ACTOR, # 항상 맵 위에 그려짐
        )

        # AI 클래스를 인스턴스화해 연결. self(이 Actor)를 넘겨서 자신을 조종하게 함
        self.ai: Optional[BaseAI] = ai_cls(self)

        self.fighter = fighter
        self.fighter.entity = self  # Fighter가 자신의 소유 엔티티를 알 수 있도록 역참조 연결

    @property
    def is_alive(self) -> bool:
        """AI가 존재하면 살아있음. die()에서 ai=None으로 만들면 False가 됨."""
        return bool(self.ai)