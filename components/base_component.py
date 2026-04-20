from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity
    from game_map import GameMap

# 모든 컴포넌트(Fighter, AI, Inventory 등)의 기본 클래스
# 컴포넌트 패턴: 기능을 Entity 안에 직접 쓰는 대신 별도 클래스로 분리해 Entity에 붙임
# 예) entity.fighter.hp, entity.ai.perform() 처럼 컴포넌트를 통해 기능에 접근
class BaseComponent:
    parent: Entity  # 이 컴포넌트를 소유한 엔티티 (초기화 시 Actor.__init__에서 연결됨)

    @property
    def gamemap(self) -> GameMap:
        """이 컴포넌트가 속한 GameMap을 반환합니다.

        동작 흐름:
        self(컴포넌트) → self.parent(Entity) → Entity.gamemap(GameMap) 순으로 참조.
        컴포넌트 안에서 맵 정보에 접근할 때 self.gamemap으로 편리하게 사용 가능.
        """
        return self.parent.gamemap

    @property
    def engine(self) -> Engine:
        """이 컴포넌트가 속한 게임 엔진을 반환합니다.

        동작 흐름:
        self.gamemap(GameMap) → GameMap.engine(Engine) 순으로 참조.
        컴포넌트 안에서 메시지 로그, 플레이어, 이벤트 핸들러 등
        엔진 전체 상태에 접근할 때 self.engine으로 편리하게 사용 가능.
        """
        return self.gamemap.engine
