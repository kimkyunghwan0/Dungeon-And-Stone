from typing import Iterable, List, Reversible, Tuple
import textwrap

import tcod

import color


# 화면에 표시될 메시지 하나를 나타내는 클래스
# 같은 메시지가 연속으로 올 때 "(x3)" 형태로 묶어서 표시 (스택 기능)
class Message:
    def __init__(self, text: str, fg: Tuple[int, int, int]):
        """메시지 객체를 초기화합니다.

        매개변수:
        - text : 메시지 내용
        - fg   : 텍스트 색상 (RGB 튜플)
        - count: 동일 메시지 반복 횟수. 처음엔 1, 같은 메시지가 이어지면 증가.
        """
        self.plain_text = text  # 실제 메시지 내용
        self.fg = fg            # 텍스트 색상 (RGB)
        self.count = 1          # 동일 메시지 반복 횟수 (스택 카운터)

    @property
    def full_text(self) -> str:
        """표시용 전체 텍스트를 반환합니다.

        동작 흐름:
        - count가 2 이상이면 원문 뒤에 "(x횟수)"를 붙여서 반환
          예) "Orc가 플레이어를 공격! 3만큼 피해를 입혔다. (x3)"
        - count가 1이면 원문 그대로 반환
        """
        if self.count > 1:
            return f"{self.plain_text} (x{self.count})"
        return self.plain_text


# 게임 내 메시지 목록을 관리하고 화면에 렌더링하는 클래스
# 전투 결과, 사망 메시지 등 게임 이벤트를 플레이어에게 알림
class MessageLog:
    def __init__(self) -> None:
        """메시지 로그를 초기화합니다. 메시지 목록은 빈 상태로 시작합니다."""
        self.messages: List[Message] = []

    def add_message(
        self, text: str, fg: Tuple[int, int, int] = color.white, *, stack: bool = True,
    ) -> None:
        """메시지를 로그에 추가합니다.

        동작 흐름:
        1. stack=True이고 마지막 메시지와 내용이 같으면 → count만 +1 증가 (중복 묶기)
           예) 같은 공격이 연속 3번 → 메시지 1개 + count=3
        2. 그 외에는 새 Message 객체를 만들어 messages 목록에 추가

        매개변수:
        - text  : 추가할 메시지 내용
        - fg    : 텍스트 색상 (기본값: 흰색)
        - stack : 중복 메시지를 묶을지 여부 (기본값: True)
        """
        if stack and self.messages and text == self.messages[-1].plain_text:
            # 같은 메시지가 반복되면 마지막 메시지의 카운트만 올림
            self.messages[-1].count += 1
        else:
            self.messages.append(Message(text, fg))

    def render(
        self, console: tcod.Console, x: int, y: int, width: int, height: int,
    ) -> None:
        """지정한 직사각형 영역에 메시지 로그를 렌더링합니다.

        동작 흐름:
        - 실제 그리기 처리를 render_messages()에 위임
        - 전체 messages 목록을 넘겨 가장 최신 메시지가 아래에 오도록 출력
        - engine.render()에서 매 프레임 호출됨
        """
        self.render_messages(console, x, y, width, height, self.messages)

    @staticmethod
    def wrap(string: str, width: int) -> Iterable[str]:
        """문자열을 width 너비에 맞게 줄 바꿈한 줄들을 순서대로 반환합니다.

        동작 흐름:
        1. string.splitlines()로 줄바꿈 문자(\n)를 먼저 분리
        2. 각 줄에 textwrap.wrap()을 적용해 width에 맞게 추가 줄 바꿈
        3. yield from으로 각 줄을 하나씩 반환 (제너레이터)

        긴 메시지가 여러 줄로 나뉘어 출력될 수 있게 해줌.
        """
        for line in string.splitlines():  # 메시지 내 줄바꿈 문자(\n)를 먼저 분리
            yield from textwrap.wrap(line, width, expand_tabs=True)

    @classmethod
    def render_messages(
        cls,
        console: tcod.Console,
        x: int,
        y: int,
        width: int,
        height: int,
        messages: Reversible[Message],
    ) -> None:
        """messages 목록을 최신 메시지가 아래에 오도록 렌더링합니다.

        동작 흐름:
        1. y_offset = height - 1 로 시작 (가장 아래 줄부터 채워 올라감)
        2. messages를 reversed()로 역순 순회 → 최신 메시지가 아래에 배치됨
        3. 각 메시지를 wrap()으로 줄 바꿈한 뒤 줄들도 reversed()로 역순 순회
           → 줄 바꿈된 줄도 위에서 아래 순서를 유지
        4. console.print()로 한 줄씩 출력하고 y_offset을 1씩 감소
        5. y_offset < 0이 되면 출력 영역이 가득 찬 것이므로 중단

        메시지 이력 뷰어(HistoryViewer)에서도 messages 슬라이스를 넘겨 재사용함.
        """
        y_offset = height - 1  # 가장 아래 줄부터 채워 올라감

        for message in reversed(messages):  # 최신 메시지가 아래에 오도록 역순 순회
            for line in reversed(list(cls.wrap(message.full_text, width))):  # 줄 바꿈된 각 줄도 역순
                console.print(x=x, y=y + y_offset, text=line, fg=message.fg)
                y_offset -= 1
                if y_offset < 0:
                    return  # 표시 영역을 다 채우면 출력 중단
