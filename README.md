기획
====================================================

[ 게임 개요 ]
이름    : Dungeon & Stone
장르    : 로그라이크 (Roguelike) RPG
언어    : Python 3.13.11
라이브러리 : tcod (로그라이크 게임 특화 라이브러리)
환경    : 파이썬 가상환경 (venv\Scripts\activate)

====================================================

[ 종족 ]
- 인간 (HUMAN)
- 드워프 (DWARF)
- 바바리안 (BARBARIAN)
- 수인 (FURRY)
- 엘프 (ELF)

====================================================

[ 화면 구성 ]
- 좌상단 : 맵 (세로 스크롤 맵)
- 우상단 : 상태창 (레벨, 생명력, 정신력, 정수, 명성, 아이템 레벨)
- 좌하단 : 채팅창
- 우하단 : 인벤토리 (기본 4x5)

====================================================

[ 개발 단계 및 진행 현황 ]

  [완료] 1장 — 기본 화면 출력
         - tcod 라이브러리 세팅
         - 터미널 창 생성 및 '@' 캐릭터 출력
         - 기본 이벤트 루프 구성

  [완료] 2장 — 플레이어 이동
         - 방향키 입력 처리 (EventHandler)
         - 플레이어 좌표 이동 구현

  [완료] 3장 — 클래스 구조 정리
         - Entity 클래스 (플레이어, 몬스터 공통 구조)
         - GameMap 클래스 (타일, 엔티티 관리)
         - Engine 클래스 (게임 루프 총괄)
         - Action 클래스 계층 구조 (Action → ActionWithDirection → Move/Melee/Bump)

  [완료] 4장 — FOV (시야각) 구현
         - compute_fov()로 플레이어 시야 계산 (반경 8)
         - visible : 현재 보이는 타일
         - explored : 이전에 본 타일 (어둡게 유지)
         - 타일 밝기 3단계 : light(시야 내) / dark(탐험함) / SHROUD(미탐험)

  [완료] 5장 — 던전 자동 생성 & 몬스터 배치
         - RectangularRoom 클래스 (방 구조)
         - generate_dungeon() : 랜덤 방 배치 + L자 복도 연결
         - place_entities() : 방마다 오크(80%) / 트롤(20%) 랜덤 배치
         - entity_factories : 플레이어, 오크, 트롤 엔티티 템플릿
         - BumpAction : 이동 방향에 적이 있으면 자동으로 공격 전환
         - MeleeAction : 근접 공격 처리

  [완료] 6장 — 전투 시스템
         - Fighter 컴포넌트 (hp, defense, power 스탯)
         - HP 프로퍼티 setter : 클램핑(0~max_hp) 및 자동 사망 처리
         - die() : 플레이어/몬스터 사망 전환 (시체 '%' 표시, AI 제거)
         - MeleeAction : power - defense 공식으로 실제 데미지 계산
         - 전투 메시지 색상 구분 (플레이어 공격 / 적 공격)

  [완료] 7장 — UI
         - render_bar() : 화면 하단 플레이어 HP 바 표시
         - MessageLog : 메시지 누적 저장 및 스크롤 렌더링
         - render_names_at_mouse_location() : 마우스 커서 위 엔티티 이름 표시
         - HistoryViewer ('v' 키) : 메시지 이력 전체 스크롤 뷰어
         - GameOverEventHandler : 사망 후 입력 차단

  [완료] 8장 — 아이템 시스템
         - Item 엔티티 / Consumable 컴포넌트 구조
         - Inventory 컴포넌트 (최대 26칸, a~z 키 선택)
         - PickupAction ('g' 키) : 발 아래 아이템 줍기
         - DropItem ('d' 키) : 인벤토리 아이템 버리기
         - HealingConsumable : 회복 포션 (체력 4 회복)
         - InventoryActivateHandler / InventoryDropHandler : 인벤토리 UI

  [완료] 9장 — 스크롤 아이템 & 메인 메뉴
         - LightningDamageConsumable : 번개 스크롤 (시야 내 최근접 적에게 20 피해, 사정거리 5)
         - FireballDamageConsumable : 파이어볼 스크롤 (범위 3칸, 12 피해, 아군 포함)
         - ConfusionConsumable : 혼란 스크롤 (10턴간 적을 무작위로 이동)
         - ConfusedEnemy AI : 혼란 상태 행동 처리 + 원래 AI 복원
         - SingleRangedAttackHandler / AreaRangedAttackHandler : 타겟 선택 커서 UI
         - MainMenu (setup_game.py) : 배경 이미지 기반 타이틀 화면 구현
         - 인게임 메시지 전면 영어화

----------------------------------------------------

  [ 예정 ] 10장 이후 — 추가 계획
         - 세이브 / 로드 기능
         - 경험치 & 레벨업 시스템
         - 종족 선택 화면 (인간, 드워프, 바바리안, 수인, 엘프)
         - 던전 층 이동 (계단)
         - 보스 몬스터
         - 성장 시스템 (정수, 명성)

====================================================

[ 현재 파일 구조 ]
  main.py               — 진입점. 게임 설정 및 메인 루프
  setup_game.py         — 새 게임 초기화, MainMenu 타이틀 화면
  engine.py             — 게임 핵심 루프 (이벤트→행동→FOV→렌더링)
  entity.py             — 엔티티 기본 클래스 (Actor, Item)
  entity_factories.py   — 플레이어/몬스터/아이템 엔티티 템플릿 정의
  game_map.py           — 맵 타일, 엔티티, 시야 관리
  input_handlers.py     — 키 입력 → 액션 변환, 각종 UI 핸들러
  actions.py            — 액션 클래스 계층 (이동, 공격, 줍기, 버리기 등)
  procgen.py            — 던전 랜덤 생성 알고리즘
  tile_types.py         — 타일 데이터 정의 (floor, wall, SHROUD)
  color.py              — 게임 전체 색상 상수
  message_log.py        — 메시지 누적 저장 및 렌더링
  render_functions.py   — HP 바, 엔티티 이름 표시 등 보조 렌더 함수
  render_order.py       — 엔티티 렌더 우선순위 (CORPSE < ITEM < ACTOR)
  exceptions.py         — Impossible, QuitWithoutSaving 예외 정의
  components/
    base_component.py   — 컴포넌트 기반 클래스 (engine, gamemap 접근)
    fighter.py          — 전투 스탯 (hp, defense, power), 사망 처리
    ai.py               — HostileEnemy, ConfusedEnemy AI
    inventory.py        — 인벤토리 (아이템 목록, 줍기/버리기)
    consumable.py       — 소비 아이템 효과 (포션, 번개/파이어볼/혼란 스크롤)

====================================================
