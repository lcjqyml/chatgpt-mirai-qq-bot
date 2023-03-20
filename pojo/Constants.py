from enum import Enum


class Constants(Enum):
    CHAT_TIMEOUT_SECONDS = 7200
    """2小时超时"""
    MAX_TOKENS = 4000
    """tokens上限"""
    V1_API = "V1"
    V2_API = "V2"
    V3_API = "V3"
    POE_API = "POE"


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


class PoeBots(Enum):
    capybara = "Sage"
    beaver = "GPT-4"
    a2_2 = "Claude+"
    a2 = "Claude"
    chinchilla = "ChatGPT"
    nutria = "Dragonfly"

    @staticmethod
    def parse(bot_name: str):
        tmp_name = bot_name.lower()
        for bot in PoeBots:
            if str(bot.name).lower() == tmp_name or str(bot.value).lower() == tmp_name:
                return bot
        return None
