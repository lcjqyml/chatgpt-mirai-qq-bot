from enum import Enum


class Constants(Enum):
    CHAT_TIMEOUT_SECONDS = 7200
    """2小时超时"""
    MAX_TOKENS = 4000
    """tokens上限"""


class InteractiveMode(Enum):
    CHAT = "chat"
    Q_A = "q&a"

    def description(self):
        if self == InteractiveMode.CHAT:
            return "聊天模式"
        elif self == InteractiveMode.Q_A:
            return "问答模式"

    @staticmethod
    def parse(mode_str: str):
        if mode_str == InteractiveMode.CHAT.value:
            return InteractiveMode.CHAT
        elif mode_str == InteractiveMode.Q_A.value:
            return InteractiveMode.Q_A
        else:
            raise Exception("Not support interactive mode -> " + mode_str)
