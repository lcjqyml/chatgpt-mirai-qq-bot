from enum import Enum


class Constants(Enum):
    CHAT_TIMEOUT_SECONDS = 7200
    """2小时超时"""


class InteractiveMode(Enum):
    CHAT = "chat"
    Q_A = "q&a"

    @staticmethod
    def parse(mode_str: str):
        if mode_str == InteractiveMode.CHAT.value:
            return InteractiveMode.CHAT
        elif mode_str == InteractiveMode.Q_A.value:
            return InteractiveMode.Q_A
        else:
            raise Exception("Not support interactive mode -> " + mode_str)
