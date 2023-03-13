from enum import Enum


class Constants(Enum):
    CHAT_TIMEOUT_SECONDS = 7200
    """2小时超时"""


class InteractiveMode(Enum):
    CHAT = "chat"
    Q_A = "q&a"

    def parse(self, mode_str: str):
        if mode_str == self.CHAT.value:
            return self.CHAT
        elif mode_str == self.Q_A.value:
            return self.Q_A
        else:
            raise Exception("Not support interactive mode -> " + mode_str)
