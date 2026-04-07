from __future__ import annotations

from typing import List, Tuple, TYPE_CHECKING

import numpy as np  # type: ignore
import tcod

from actions import Action, MeleeAction, MovementAction, WaitAction
from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor

# 모든 AI의 기본 클래스
# Action과 BaseComponent를 동시에 상속:
#   - Action  → perform()으로 매 턴 행동 실행
#   - BaseComponent → self.engine, self.entity로 게임 상태 접근
class BaseAI(Action, BaseComponent):
    entity: Actor

    def perform(self) -> None:
        raise NotImplementedError()  # 하위 AI 클래스에서 반드시 구현

    def get_path_to(self, dest_x: int, dest_y: int) -> List[Tuple[int, int]]:
        """목표 좌표까지의 경로를 계산해 반환합니다. 경로가 없으면 빈 리스트 반환."""

        # 맵의 walkable 배열을 복사해 이동 비용(cost) 배열로 사용
        # cost가 0인 칸 = 벽(이동 불가), 1 이상 = 이동 가능
        cost = np.array(self.entity.gamemap.tiles["walkable"], dtype=np.int8)

        for entity in self.entity.gamemap.entities:
            # 이동을 막는 엔티티가 있는 칸의 비용을 올림
            if entity.blocks_movement and cost[entity.x, entity.y]:
                # 비용을 높이면 AI가 다른 적들을 피해 더 긴 경로를 선택함
                # 값이 낮으면 좁은 복도에서 적들이 줄 서서 몰림
                # 값이 높으면 적들이 우회해 플레이어를 포위하려 함
                cost[entity.x, entity.y] += 10

        # cost 배열로 그래프를 생성하고 경로탐색기(Pathfinder)에 전달
        # cardinal=2 : 상하좌우 이동 비용, diagonal=3 : 대각선 이동 비용
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)

        pathfinder.add_root((self.entity.x, self.entity.y))  # 현재 위치를 시작점으로 설정

        # 목표 좌표까지 경로 계산. [1:]로 시작점(현재 위치)을 제외
        path: List[List[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

        # List[List[int]] → List[Tuple[int, int]] 형식으로 변환해 반환
        return [(index[0], index[1]) for index in path]


# 적대적 AI — 플레이어를 발견하면 추적하고 인접하면 공격
class HostileEnemy(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []  # 현재 추적 중인 경로 (좌표 목록)

    def perform(self) -> None:
        target = self.engine.player
        dx = target.x - self.entity.x  # 플레이어까지의 x 거리
        dy = target.y - self.entity.y  # 플레이어까지의 y 거리

        # 체비쇼프 거리(Chebyshev distance): 대각선 이동을 1칸으로 계산하는 거리 방식
        # max(|dx|, |dy|) == 1이면 바로 옆에 있다는 뜻
        distance = max(abs(dx), abs(dy))

        # 이 적이 플레이어의 시야 안에 있을 때만 행동 (시야 밖이면 제자리 대기)
        if self.engine.game_map.visible[self.entity.x, self.entity.y]:
            if distance <= 1:
                # 플레이어가 바로 옆 → 근접 공격
                return MeleeAction(self.entity, dx, dy).perform()

            # 플레이어가 멀리 있음 → 경로 재계산
            self.path = self.get_path_to(target.x, target.y)

        if self.path:
            # 저장된 경로의 다음 좌표로 한 칸 이동
            dest_x, dest_y = self.path.pop(0)
            return MovementAction(
                self.entity,
                dest_x - self.entity.x,  # 다음 칸까지의 dx
                dest_y - self.entity.y,  # 다음 칸까지의 dy
            ).perform()

        # 경로도 없고 시야 밖이면 제자리 대기
        return WaitAction(self.entity).perform()
