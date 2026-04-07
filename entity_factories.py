from components.ai import HostileEnemy
from components.fighter import Fighter
from entity import Actor

# 게임에 등장하는 엔티티 원본(템플릿)을 정의
# 실제 사용 시 spawn()으로 복사본을 생성하므로 이 원본은 변경되지 않음

# 플레이어 — '@' 기호, 흰색 / HP:30, 방어:2, 공격:5
# ai_cls=HostileEnemy 이지만 플레이어는 키보드로 조작하므로 AI가 실제로 실행되지 않음
player = Actor(
    char="@",
    color=(255, 255, 255),
    name="Player",
    ai_cls=HostileEnemy,
    fighter=Fighter(hp=30, defense=2, power=5),
)

# 오크 — 'o' 기호, 녹색 계열. 80% 확률로 등장하는 일반 몬스터
orc = Actor(
    char="o",
    color=(63, 127, 63),
    name="Orc",
    ai_cls=HostileEnemy,
    fighter=Fighter(hp=10, defense=0, power=3),
)

# 트롤 — 'T' 기호, 진한 녹색. 20% 확률로 등장하는 강한 몬스터
troll = Actor(
    char="T",
    color=(0, 127, 0),
    name="Troll",
    ai_cls=HostileEnemy,
    fighter=Fighter(hp=16, defense=1, power=4),
)
