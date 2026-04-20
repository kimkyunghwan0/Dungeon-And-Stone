from components.ai import HostileEnemy
from components import consumable
from components.fighter import Fighter
from components.inventory import Inventory
from entity import Actor, Item

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
    inventory=Inventory(capacity=26),
)

# 오크 — 'o' 기호, 녹색 계열. 80% 확률로 등장하는 일반 몬스터
orc = Actor(
    char="o",
    color=(63, 127, 63),
    name="Orc",
    ai_cls=HostileEnemy,
    fighter=Fighter(hp=10, defense=0, power=3),
    inventory=Inventory(capacity=0),
)

# 트롤 — 'T' 기호, 진한 녹색. 20% 확률로 등장하는 강한 몬스터
troll = Actor(
    char="T",
    color=(0, 127, 0),
    name="Troll",
    ai_cls=HostileEnemy,
    fighter=Fighter(hp=16, defense=1, power=4),
    inventory=Inventory(capacity=0),
)

# 혼란스크롤 - '10턴간 상대에게 혼란 상태이상 부여'
confusion_scroll = Item(
    char="~",
    color=(207, 63, 255),
    name="Confusion Scroll",
    consumable=consumable.ConfusionConsumable(number_of_turns=10),
)

# 파이어볼스크롤 - '12데미지를 3칸의 범위로 준다.'
fireball_scroll = Item( 
    char="~", 
    color=(255, 0, 0), 
    name="Fireball Scroll", 
    consumable=consumable.FireballDamageConsumable(damage=12, radius=3), 
) 

# 회복 포션 ㅡ 체력 4만큼 회복
health_potion = Item(
    char="!",
    color=(127, 0, 255),
    name="Health Potion",
    consumable=consumable.HealingConsumable(amount=4),
)

# 번개 스크롤 — 시야 내 가장 가까운 적에게 20 데미지를 주는 범위 5의 번개
lightning_scroll = Item(
    char="~",
    color=(255, 255, 0),
    name="Lightning Scroll",
    consumable=consumable.LightningDamageConsumable(damage=20, maximum_range=5),
)