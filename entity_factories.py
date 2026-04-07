from entity import Entity

# 게임에 등장하는 엔티티 원본(템플릿)을 정의
# 실제 사용 시 spawn()으로 복사본을 생성하므로 이 원본은 변경되지 않음

# 플레이어 — '@' 기호, 흰색
player = Entity(char="@", color=(255, 255, 255), name="Player", blocks_movement=True)

# 오크 — 'o' 기호, 녹색 계열. 80% 확률로 등장하는 일반 몬스터
orc = Entity(char="o", color=(63, 127, 63), name="Orc", blocks_movement=True)

# 트롤 — 'T' 기호, 진한 녹색. 20% 확률로 등장하는 강한 몬스터
troll = Entity(char="T", color=(0, 127, 0), name="Troll", blocks_movement=True)