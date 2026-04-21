class Impossible(Exception):
    """ 행동을 수행할 수 없을 때 제기되는 예외. 
        그 이유는 예외 메시지로 주어집니다
    """
class QuitWithoutSaving(SystemExit):
    """자동 저장 없이 게임을 종료하기 위해 발생할 수 있는 예외입니다."""