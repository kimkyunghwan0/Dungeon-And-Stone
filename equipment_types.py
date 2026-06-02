# 장비 슬롯의 종류(무기·방어구)를 열거형으로 정의합니다.
from enum import auto, Enum


# 장비 슬롯 종류 — Equipment 컴포넌트에서 어느 슬롯에 장착할지 결정할 때 사용
class EquipmentType(Enum):
    WEAPON = auto()  # 무기 슬롯
    ARMOR = auto()   # 방어구 슬롯
