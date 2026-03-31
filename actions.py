# 액션
class Action:
    pass

# Esc 키
class EscapeAction(Action):
    pass

# 동작
class MovementAction(Action):
    def __init__(self, dx: int, dy: int):
        super().__init__()

        self.dx = dx
        self.dy = dy