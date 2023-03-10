from typing import Tuple
from config import Config, OpenAIAuths
import asyncio
from manager import BotManager, BotInfo
import atexit
from loguru import logger
from datetime import datetime

config = Config.load_config()
if type(config.openai) is OpenAIAuths:
    botManager = BotManager(config.openai.accounts)
else:
    # Backward-compatibility
    botManager = BotManager([config.openai])


def setup():
    botManager.login()


class ChatSession:
    chatbot: BotInfo = None
    session_id: str
    api_version: str = None

    def __init__(self, session_id, api_version: str = None):
        self.session_id = session_id
        self.prev_conversation_id = []
        self.prev_parent_id = []
        self.parent_id = None
        self.conversation_id = None
        self.api_version = api_version
        self.reset_conversation()

    def is_v1_api(self) -> bool:
        return self.api_version == "V1"

    def is_v2_api(self) -> bool:
        return self.api_version == "V2"

    def is_v3_api(self) -> bool:
        return self.api_version == "V3"

    """重置会话"""
    def reset_conversation(self):
        self.chatbot = botManager.pick(self.api_version)
        if self.is_v1_api():
            self.chatbot.reset(self.conversation_id)
            self.conversation_id = None
            self.parent_id = None
            self.prev_conversation_id = []
            self.prev_parent_id = []
        elif self.is_v3_api():
            self.chatbot.reset(self.session_id)

    """向 revChatGPT.V1 发送提问"""
    def v1_ask(self, prompt, conversation_id=None, parent_id=None):
        resp = self.chatbot.bot.ask(prompt=prompt, conversation_id=conversation_id, parent_id=parent_id)
        final_resp = None
        for final_resp in resp:
            pass
        if final_resp is None:
            raise Exception("OpenAI 在返回结果时出现了错误")
        return final_resp

    """向 revChatGPT.V3 发送提问"""
    def v3_ask(self, prompt):
        return self.chatbot.bot.ask(prompt=prompt, convo_id=self.session_id)

    """回滚会话"""
    def rollback_conversation(self) -> bool:
        if self.is_v1_api():
            if len(self.prev_parent_id) <= 0:
                return False
            self.conversation_id = self.prev_conversation_id.pop()
            self.parent_id = self.prev_parent_id.pop()
        elif self.is_v3_api():
            conversation_size = len(self.chatbot.bot.conversation[self.session_id])
            if conversation_size > 2:
                self.chatbot.bot.rollback(2, convo_id=self.session_id)
            elif conversation_size == 2:
                self.chatbot.bot.rollback(1, convo_id=self.session_id)
        return True

    async def get_chat_response(self, message) -> str:
        loop = asyncio.get_event_loop()
        if self.is_v1_api():
            self.prev_conversation_id.append(self.conversation_id)
            self.prev_parent_id.append(self.parent_id)
            bot = self.chatbot.bot
            bot.conversation_id = self.conversation_id
            bot.parent_id = self.parent_id
            resp = await loop.run_in_executor(None, self.v1_ask, message, self.conversation_id, self.parent_id)
            self.conversation_id = resp["conversation_id"]
            if self.conversation_id is None and self.chatbot.account.title_pattern:
                self.chatbot.bot.change_title(self.conversation_id,
                                              self.chatbot.account.title_pattern.format(session_id=self.session_id))
            self.parent_id = resp["parent_id"]
            return resp["message"]
        elif self.is_v3_api():
            resp = await loop.run_in_executor(None, self.v3_ask, message)
            return resp


__sessions = {}


def get_chat_session(session_id: str, api_version: str = None) -> Tuple[ChatSession, bool]:
    new_session = False
    if session_id not in __sessions:
        __sessions[session_id] = ChatSession(session_id, api_version)
        new_session = True
    return __sessions[session_id], new_session


def conversation_remover():
    logger.info("删除会话中……")
    for session in __sessions.values():
        if session.chatbot.account.auto_remove_old_conversations and session.chatbot and session.conversation_id:
            try:
                session.chatbot.bot.delete_conversation(session.conversation_id)
            except Exception as e:
                logger.error(f"删除会话 {session.conversation_id} 失败：{str(e)}")


atexit.register(conversation_remover)
