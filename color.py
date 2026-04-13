# 게임 전체에서 사용하는 색상 상수 모음 (RGB 튜플 형식)

# 기본 색상
white = (0xFF, 0xFF, 0xFF)  # 흰색
black = (0x0, 0x0, 0x0)     # 검정색

# 전투 메시지 색상
player_atk = (0xE0, 0xE0, 0xE0)  # 플레이어 공격 메시지 — 밝은 회색
enemy_atk  = (0xFF, 0xC0, 0xC0)  # 적 공격 메시지 — 연분홍색

# 사망 메시지 색상
player_die = (0xFF, 0x30, 0x30)  # 플레이어 사망 — 선명한 빨강
enemy_die  = (0xFF, 0xA0, 0x30)  # 적 사망 — 주황색

welcome_text = (0x20, 0xA0, 0xFF)  # 시작 환영 메시지 — 하늘색

# HP 바 색상
bar_text   = white              # HP 수치 텍스트 — 흰색
bar_filled = (0x0, 0x60, 0x0)  # HP 채워진 부분 — 진한 초록
bar_empty  = (0x40, 0x10, 0x10)  # HP 빈 부분 — 어두운 빨강