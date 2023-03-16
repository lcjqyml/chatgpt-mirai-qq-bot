import asyncio
import atexit
from datetime import datetime

from loguru import logger

from config import Config, OpenAIAuths
from manager import BotManager, BotInfo
from pojo.Constants import InteractiveMode, Constants

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
    interactive_mode: InteractiveMode = None
    default_interactive_mode: InteractiveMode = None

    def __init__(self, session_id, api_version: str = None):
        self.last_operation_time = None
        self.session_id = session_id
        self.prev_conversation_id = []
        self.prev_parent_id = []
        self.parent_id = None
        self.conversation_id = None
        self.api_version = api_version if api_version else None
        self.reset_conversation()

    def is_chat_mode(self) -> bool:
        return self.interactive_mode == InteractiveMode.CHAT

    def is_qa_mode(self) -> bool:
        return self.interactive_mode == InteractiveMode.Q_A

    def is_v1_api(self) -> bool:
        return self.api_version == Constants.V1_API.value

    def is_v2_api(self) -> bool:
        return self.api_version == Constants.V2_API.value

    def is_v3_api(self) -> bool:
        return self.api_version == Constants.V3_API.value

    def get_status(self) -> str:
        """获取session状态"""
        last_operation_time_str = self.last_operation_time.strftime("%Y-%m-%d %H:%M:%S") if self.last_operation_time \
            else "无"
        if self.is_v1_api():
            return config.response.ping_v1.format(session_id=self.session_id, api_version=self.api_version,
                                                  last_operation_time=last_operation_time_str)
        elif self.is_v3_api():
            interactive_mode_str = self.interactive_mode.description()
            return config.response.ping_v3.format(session_id=self.session_id, api_version=self.api_version,
                                                  last_operation_time=last_operation_time_str,
                                                  interactive_mode=interactive_mode_str,
                                                  api_model=self.chatbot.bot.engine,
                                                  current_token_count=self.chatbot.bot.get_token_count(self.session_id),
                                                  max_token_count=self.chatbot.bot.max_tokens,
                                                  system_prompt=self.get_system_prompt())
        return f"Not support version {self.api_version}"

    def reset_conversation(self, interactive_mode: InteractiveMode = None):
        """重置会话"""
        self.chatbot = botManager.pick(self.api_version)
        self.api_version = self.chatbot.api_version
        self.default_interactive_mode = InteractiveMode.parse(mode_str=self.chatbot.account.default_interactive_mode)
        self.last_operation_time = None
        if self.is_v1_api():
            self.chatbot.reset(self.conversation_id)
            self.conversation_id = None
            self.parent_id = None
            self.prev_conversation_id = []
            self.prev_parent_id = []
        elif self.is_v3_api():
            self.interactive_mode = interactive_mode if interactive_mode else self.default_interactive_mode
            self.chatbot.reset(convo_id=self.session_id, no_system_prompt=self.is_qa_mode())

    def get_system_prompt(self):
        """获取system_prompt"""
        if self.is_v3_api():
            return next((item["content"] for item in self.chatbot.bot.conversation[self.session_id] if
                         item["role"] == "system"), "无")
        else:
            return "无"

    def v1_ask(self, prompt, conversation_id=None, parent_id=None):
        """向 revChatGPT.V1 发送提问"""
        resp = self.chatbot.bot.ask(prompt=prompt, conversation_id=conversation_id, parent_id=parent_id)
        final_resp = None
        for final_resp in resp:
            pass
        if final_resp is None:
            raise Exception("OpenAI 在返回结果时出现了错误")
        return final_resp

    def v3_ask(self, prompt):
        """向 revChatGPT.V3 发送提问"""
        if self.is_qa_mode():
            self.chatbot.bot.rollback(len(self.chatbot.bot.conversation[self.session_id]), convo_id=self.session_id)
        return self.chatbot.bot.ask(prompt=prompt, convo_id=self.session_id)

    def rollback_conversation(self) -> bool:
        """回滚会话"""
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

    def check_and_reset_conversation(self):
        """会话超时就重置，重新发起"""
        if self.last_operation_time is None:
            return
        current_time = datetime.now()
        time_diff = current_time - self.last_operation_time
        if time_diff.total_seconds() > Constants.CHAT_TIMEOUT_SECONDS.value:
            self.reset_conversation()

    async def get_chat_response(self, message) -> str:
        self.check_and_reset_conversation()
        try:
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
        finally:
            self.last_operation_time = datetime.now()


__sessions = {}


def get_chat_session(session_id: str, api_version: str = None) -> ChatSession:
    if session_id not in __sessions:
        __sessions[session_id] = ChatSession(session_id, api_version)
    session: ChatSession = __sessions[session_id]
    if api_version is not None and session.api_version != api_version:
        __sessions[session_id] = ChatSession(session_id, api_version)
        session: ChatSession = __sessions[session_id]
    session.check_and_reset_conversation()
    return session


def conversation_remover():
    logger.info("删除会话中……")
    for session in __sessions.values():
        if session.chatbot and session.conversation_id:
            try:
                session.chatbot.bot.delete_conversation(session.conversation_id)
            except Exception as e:
                logger.error(f"删除会话 {session.conversation_id} 失败：{str(e)}")


atexit.register(conversation_remover)
