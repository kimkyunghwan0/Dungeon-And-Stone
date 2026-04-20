from __future__ import annotations

import copy
import math
from typing import Optional, Tuple, Type, TypeVar, TYPE_CHECKING, Union

from render_order import RenderOrder

if TYPE_CHECKING:
    from components.ai import BaseAI
    from components.consumable import Consumable
    from components.fighter import Fighter
    from components.inventory import Inventory
    from game_map import GameMap

# Entity 하위 클래스도 spawn()에서 올바른 타입을 반환받기 위한 제네릭 타입 변수
# 예: Actor.spawn()이 Entity가 아닌 Actor 타입으로 반환되도록 보장
T = TypeVar("T", bound="Entity")


# 플레이어, 적, 아이템 등을 나타내는 일반적인 객체
class Entity:
    # 클래스 변수 선언 — __init__에서 gamemap이 제공되지 않을 수도 있으므로
    # 타입 힌트만 선언하고 실제 할당은 나중에 함 (gamemap 없이 생성 후 나중에 연결)
    parent: Union[GameMap, Inventory]

    def __init__(
        self,
        parent: Optional[GameMap] = None,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        blocks_movement: bool = False,
        render_order: RenderOrder = RenderOrder.CORPSE,
    ):
        """엔티티를 초기화합니다.

        매개변수:
        - parent         : 이 엔티티가 속한 GameMap (없으면 나중에 spawn/place로 연결)
        - x, y           : 맵 위 좌표
        - char           : 화면에 표시할 문자 (예: '@', 'o', '!')
        - color          : 문자 색상 (RGB 튜플)
        - name           : 엔티티 이름 (마우스 호버 시 표시)
        - blocks_movement: True이면 다른 엔티티가 이 칸으로 이동 불가
        - render_order   : 렌더링 우선순위 (CORPSE < ITEM < ACTOR, 값이 높을수록 위에 그려짐)

        parent가 주어지면 즉시 해당 맵의 entities에 자신을 추가.
        """
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks_movement = blocks_movement
        self.render_order = render_order

        if parent:
            # parent 제공된 경우 즉시 연결. 아니면 나중에 spawn()이나 place()로 연결
            self.parent = parent
            parent.entities.add(self)

    @property
    def gamemap(self) -> GameMap:
        """이 엔티티가 속한 GameMap을 반환합니다.

        parent가 GameMap이면 직접 반환, Inventory이면 Inventory.gamemap을 따라 올라감.
        컴포넌트(Fighter, AI 등)에서도 entity.gamemap으로 맵에 접근할 수 있게 해줌.
        """
        return self.parent.gamemap

    def spawn(self: T, gamemap: GameMap, x: int, y: int) -> T:
        """주어진 위치에 이 인스턴스의 복사본을 생성하고 반환합니다.

        동작 흐름:
        1. copy.deepcopy()로 원본 엔티티를 완전히 복사 (스탯, 컴포넌트 포함)
        2. 복사본의 좌표를 (x, y)로 설정
        3. 복사본의 parent를 gamemap으로 연결
        4. gamemap.entities에 복사본을 추가

        entity_factories에 정의된 원본은 절대 변경되지 않으므로,
        같은 종류의 몬스터를 여러 번 소환해도 각각 독립적인 인스턴스를 가짐.
        """
        clone = copy.deepcopy(self)  # 원본 엔티티를 깊은 복사 (독립적인 새 인스턴스)
        clone.x = x
        clone.y = y
        clone.parent = gamemap
        gamemap.entities.add(clone)  # 맵의 엔티티 집합에 추가
        return clone

    def place(self, x: int, y: int, gamemap: Optional[GameMap] = None) -> None:
        """이 엔티티를 새 위치에 배치합니다.

        동작 흐름:
        1. 좌표를 (x, y)로 갱신
        2. gamemap이 주어지고, 현재 parent가 어떤 GameMap이라면 기존 맵에서 자신을 제거
        3. parent를 새 gamemap으로 교체하고 새 맵의 entities에 추가

        층 이동이나 아이템 버리기처럼 엔티티의 소속 맵을 바꿀 때 사용.
        gamemap을 생략하면 좌표만 갱신 (같은 맵 안에서 순간이동).
        """
        self.x = x
        self.y = y
        if gamemap:
            if hasattr(self, "parent"):  # gamemap이 아직 초기화되지 않았을 수 있음
                if self.parent is self.gamemap:
                    self.gamemap.entities.remove(self)  # 기존 맵에서 제거
            self.parent = gamemap
            gamemap.entities.add(self)  # 새 맵에 추가

    def distance(self, x: int, y: int) -> float:
        """현재 위치에서 주어진 (x, y) 좌표까지의 유클리드 거리를 반환합니다.

        유클리드 거리 = sqrt((x2-x1)² + (y2-y1)²)
        번개 스크롤의 최근접 적 탐색, 파이어볼의 범위 판정 등에 사용.
        대각선 이동은 max(|dx|, |dy|)로 계산하는 체비쇼프 거리와 다름에 주의.
        """
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def move(self, dx: int, dy: int) -> None:
        """엔티티를 (dx, dy)만큼 이동합니다.

        현재 좌표에 방향 벡터를 더해 좌표를 갱신.
        이동 가능 여부 검사는 MovementAction.perform()에서 미리 완료된 상태로 호출됨.
        """
        self.x += dx
        self.y += dy


# 행동(AI)과 전투 능력(Fighter)을 가진 살아있는 캐릭터 (플레이어, 몬스터)
# Entity를 상속하며, blocks_movement=True와 render_order=ACTOR가 기본값
class Actor(Entity):
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
        inventory: Inventory,
    ):
        """Actor를 초기화합니다.

        매개변수:
        - ai_cls   : 사용할 AI 클래스 타입 (인스턴스가 아닌 클래스를 받아서 여기서 인스턴스화)
        - fighter  : 전투 스탯 컴포넌트 (HP, 공격력, 방어력)
        - inventory: 인벤토리 컴포넌트 (아이템 목록 관리)

        동작 흐름:
        1. Entity.__init__()로 기본 속성 초기화 (blocks_movement=True, render_order=ACTOR 고정)
        2. ai_cls(self)로 AI 인스턴스를 생성하고 연결 (자신을 인자로 넘겨 AI가 자신을 조종)
        3. fighter.parent = self 로 Fighter가 자신의 소유 Actor를 역참조할 수 있도록 연결
        4. inventory.parent = self 로 동일하게 연결
        """
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=True,           # 살아있는 캐릭터는 항상 이동을 막음
            render_order=RenderOrder.ACTOR, # 항상 맵 위에 그려짐
        )

        # AI 클래스를 인스턴스화해 연결. self(이 Actor)를 넘겨서 자신을 조종하게 함
        self.ai: Optional[BaseAI] = ai_cls(self)

        self.fighter = fighter
        self.fighter.parent = self  # Fighter가 자신의 소유 엔티티를 알 수 있도록 역참조 연결

        self.inventory = inventory
        self.inventory.parent = self

    @property
    def is_alive(self) -> bool:
        """이 Actor가 살아있으면 True를 반환합니다.

        ai가 None이 아니면 살아있는 것으로 간주.
        Fighter.die()에서 self.parent.ai = None 으로 만들면 False가 됨.
        handle_enemy_turns()에서 살아있는 적만 행동하도록 필터링할 때 사용.
        """
        return bool(self.ai)


class Item(Entity):
    def __init__(
        self,
        *,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        consumable: Consumable,
    ):
        """아이템 엔티티를 초기화합니다.

        매개변수:
        - consumable : 아이템 효과를 담당하는 컴포넌트
                       (HealingConsumable, LightningDamageConsumable 등)

        동작 흐름:
        1. Entity.__init__()로 기본 속성 초기화
           (blocks_movement=False → 아이템 위로 걸어다닐 수 있음, render_order=ITEM)
        2. consumable.parent = self 로 역참조 연결
           (consumable 안에서 self.parent로 아이템 자체에 접근 가능)
        """
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=False,
            render_order=RenderOrder.ITEM,
        )

        self.consumable = consumable
        self.consumable.parent = self
