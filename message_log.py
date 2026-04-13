from typing import List, Reversible, Tuple
import textwrap

import tcod

import color


# 화면에 표시될 메시지 하나를 나타내는 클래스
# 같은 메시지가 연속으로 올 때 "(x3)" 형태로 묶어서 표시 (스택 기능)
class Message:
    def __init__(self, text: str, fg: Tuple[int, int, int]):
        self.plain_text = text  # 실제 메시지 내용
        self.fg = fg            # 텍스트 색상 (RGB)
        self.count = 1          # 동일 메시지 반복 횟수 (스택 카운터)

    @property
    def full_text(self) -> str:
        """count가 2 이상이면 "(x횟수)"를 붙여서 반환, 아니면 원문 그대로 반환."""
        if self.count > 1:
            return f"{self.plain_text} (x{self.count})"
        return self.plain_text


# 게임 내 메시지 목록을 관리하고 화면에 렌더링하는 클래스
# 전투 결과, 사망 메시지 등 게임 이벤트를 플레이어에게 알림
class MessageLog:
    def __init__(self) -> None:
        self.messages: List[Message] = []  # 누적된 메시지 목록

    def add_message(
        self, text: str, fg: Tuple[int, int, int] = color.white, *, stack: bool = True,
    ) -> None:
        """메시지를 로그에 추가합니다.

        stack=True이고 직전 메시지와 내용이 같으면 count만 증가 (중복 메시지 묶기)
        stack=False이거나 내용이 다르면 새 Message 객체로 추가
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

        실제 그리기는 render_messages()에 위임.
        외부에서는 이 메서드만 호출하면 됨.
        """
        self.render_messages(console, x, y, width, height, self.messages)

    @staticmethod
    def render_messages(
        console: tcod.Console,
        x: int,
        y: int,
        width: int,
        height: int,
        messages: Reversible[Message],
    ) -> None:
        """messages 목록을 최신 메시지가 아래에 오도록 역순으로 렌더링합니다.

        긴 메시지는 textwrap.wrap()으로 width에 맞게 줄 바꿈.
        y_offset을 아래(height-1)에서 위로 줄여가며 출력 — 공간이 없으면 중단.
        """
        y_offset = height - 1  # 가장 아래 줄부터 채워 올라감

        for message in reversed(messages):  # 최신 메시지가 아래에 오도록 역순 순회
            for line in reversed(textwrap.wrap(message.full_text, width)):  # 줄 바꿈된 각 줄도 역순
                console.print(x=x, y=y + y_offset, text=line, fg=message.fg)
                y_offset -= 1
                if y_offset < 0:
                    return  # 표시 영역을 다 채우면 출력 중단
