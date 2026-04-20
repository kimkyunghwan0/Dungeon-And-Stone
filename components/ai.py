from __future__ import annotations

from typing import List, Optional, Tuple, TYPE_CHECKING

import random
import numpy as np  # type: ignore
import tcod

from actions import Action, BumpAction, MeleeAction, MovementAction, WaitAction

if TYPE_CHECKING:
    from entity import Actor

# 모든 AI의 기본 클래스
# Action을 상속해 perform()으로 매 턴 행동을 실행하고,
# self.entity / self.engine 으로 게임 상태에 접근함
class BaseAI(Action):

    def perform(self) -> None:
        """매 턴 AI의 행동을 실행합니다. 하위 AI 클래스에서 반드시 구현해야 합니다."""
        raise NotImplementedError()

    def get_path_to(self, dest_x: int, dest_y: int) -> List[Tuple[int, int]]:
        """현재 위치에서 목표 좌표까지의 이동 경로를 계산해 반환합니다.

        동작 흐름:
        1. 맵의 walkable 배열을 복사해 이동 비용(cost) 배열 생성
           - walkable=0인 칸(벽) → cost=0 → 이동 불가
           - walkable=1인 칸(바닥) → cost=1 → 이동 가능
        2. 이동을 막는 엔티티(blocks_movement=True)가 있는 칸의 비용을 +10 증가
           - 비용을 높이면 AI가 다른 적들을 피해 더 긴 우회 경로를 선택함
           - 좁은 복도에서 여러 적이 줄 서지 않고 분산해 포위하려 함
        3. tcod.path.SimpleGraph로 비용 배열 기반의 이동 그래프를 생성
           - cardinal=2 : 상하좌우 이동 비용
           - diagonal=3 : 대각선 이동 비용 (대각선이 약간 더 비쌈)
        4. Pathfinder로 현재 위치에서 목표까지의 최단 경로 계산
        5. 경로의 첫 번째 좌표(현재 위치)를 제외하고 List[Tuple] 형태로 반환
           경로가 없으면 빈 리스트 반환.
        """
        # 맵의 walkable 배열을 복사해 이동 비용(cost) 배열로 사용
        cost = np.array(self.entity.gamemap.tiles["walkable"], dtype=np.int8)

        for entity in self.entity.gamemap.entities:
            # 이동을 막는 엔티티가 있는 칸의 비용을 올려 우회 경로를 유도
            if entity.blocks_movement and cost[entity.x, entity.y]:
                cost[entity.x, entity.y] += 10

        # cost 배열로 그래프를 생성하고 경로탐색기(Pathfinder)에 전달
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)

        pathfinder.add_root((self.entity.x, self.entity.y))  # 현재 위치를 시작점으로 설정

        # 목표 좌표까지 경로 계산. [1:]로 시작점(현재 위치)을 제외
        path: List[List[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

        # List[List[int]] → List[Tuple[int, int]] 형식으로 변환해 반환
        return [(index[0], index[1]) for index in path]


# 적대적 AI — 플레이어를 시야 안에서 발견하면 추적하고, 인접하면 공격
class HostileEnemy(BaseAI):
    def __init__(self, entity: Actor):
        """AI를 초기화합니다.

        path : 플레이어를 향한 현재 추적 경로 (좌표 목록).
               매 턴 시야 안에 있을 때 get_path_to()로 갱신됨.
               경로를 캐시해 두므로 시야 밖으로 사라져도 마지막 경로를 따라 이동.
        """
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []

    def perform(self) -> None:
        """매 턴 상황에 따라 공격, 추적, 대기 중 하나를 수행합니다.

        동작 흐름:
        1. 플레이어까지의 dx, dy를 계산
        2. 체비쇼프 거리(max(|dx|,|dy|)) 계산
           - distance=1 이면 바로 옆에 있는 것 (대각선 포함)
        3. 이 적이 플레이어의 시야(visible) 안에 있을 때만 반응
           - distance ≤ 1 → MeleeAction(근접 공격)
           - distance > 1 → get_path_to()로 경로 재계산
        4. 저장된 경로(self.path)가 있으면 다음 좌표로 한 칸 이동
           - path.pop(0): 경로 맨 앞 좌표를 꺼내 이동 후 경로에서 제거
        5. 경로도 없고 시야 밖이면 WaitAction(제자리 대기)
        """
        target = self.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y

        # 체비쇼프 거리: 대각선 이동을 1칸으로 계산
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


# 혼란 상태 AI — 지정된 턴 동안 무작위 방향으로 움직이다가 원래 AI로 복귀
class ConfusedEnemy(BaseAI):
    """
    혼란 상태의 적은 지정된 턴 수 동안 무작위로 이동하며,
    이동하려는 칸에 다른 액터가 있으면 무작위 방향으로 공격합니다.
    효과가 끝나면 원래 AI로 복귀합니다.
    """

    def __init__(
        self, entity: Actor, previous_ai: Optional[BaseAI], turns_remaining: int
    ):
        """혼란 AI를 초기화합니다.

        매개변수:
        - previous_ai    : 혼란 전 원본 AI (효과 종료 후 복원에 사용)
        - turns_remaining: 혼란 상태 남은 턴 수
        """
        super().__init__(entity)
        self.previous_ai = previous_ai
        self.turns_remaining = turns_remaining

    def perform(self) -> None:
        """매 턴 혼란 상태를 처리합니다.

        동작 흐름:
        1. turns_remaining이 0 이하면 혼란 종료
           - 메시지 출력 후 entity.ai를 previous_ai로 복원
        2. 아직 남은 턴이 있으면:
           - 8방향 중 하나를 random.choice()로 무작위 선택
           - turns_remaining을 1 감소
           - BumpAction으로 선택된 방향을 시도
             (벽이면 이동 실패 + 턴 낭비, 적이 있으면 공격)
        """
        if self.turns_remaining <= 0:
            self.engine.message_log.add_message(
                f"{self.entity.name}의 혼란이 풀렸다."
            )
            self.entity.ai = self.previous_ai
        else:
            # 8방향 중 하나를 무작위로 선택
            direction_x, direction_y = random.choice(
                [
                    (-1, -1),  # 좌상단
                    (0, -1),   # 위
                    (1, -1),   # 우상단
                    (-1, 0),   # 왼쪽
                    (1, 0),    # 오른쪽
                    (-1, 1),   # 좌하단
                    (0, 1),    # 아래
                    (1, 1),    # 우하단
                ]
            )

            self.turns_remaining -= 1

            # 선택된 방향으로 이동 또는 공격을 시도 (벽이면 한 턴 낭비됨)
            return BumpAction(self.entity, direction_x, direction_y).perform()
