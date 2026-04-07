from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity

# 모든 컴포넌트(Fighter, AI 등)의 기본 클래스
# 컴포넌트 패턴: 기능을 Entity 안에 직접 쓰는 대신 별도 클래스로 분리해 Entity에 붙임
# 예) entity.fighter.hp, entity.ai.perform() 처럼 사용
class BaseComponent:
    entity: Entity  # 이 컴포넌트를 소유한 엔티티 (Fighter나 AI가 초기화될 때 연결됨)

    @property
    def engine(self) -> Engine:
        # 엔티티 → 맵 → 엔진 순으로 참조해 현재 엔진에 접근
        return self.entity.gamemap.engine