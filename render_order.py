from enum import auto, Enum

# auto() == 자동으로 증가하는 정수값 유형
# 엔티티를 화면에 그리는 순서(우선순위)를 정의
# 값이 낮을수록 먼저 그려지므로(뒤에 깔림), 높을수록 위에 표시됨
# 예: 시체(CORPSE) 위에 아이템(ITEM)이, 아이템 위에 캐릭터(ACTOR)가 그려짐
class RenderOrder(Enum):
    CORPSE = auto()  # 시체 — 가장 먼저 그려져 바닥에 깔림
    ITEM   = auto()  # 아이템 — 시체 위에 표시
    ACTOR  = auto()  # 살아있는 캐릭터(플레이어, 몬스터) — 가장 위에 표시