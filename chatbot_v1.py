import asyncio
import os

from loguru import logger
from revChatGPT.V1 import Chatbot

from config import Config

config = Config.load_config()

os.environ.setdefault('TEMPERATURE', str(config.openai.temperature))

bot = None


def setup():
    global bot
    if not (config.openai.email and config.openai.password):
        logger.error("配置文件出错！请配置 OpenAI 的邮箱、密码。")
        exit(-1)
    if config.openai.proxy:
        bot = Chatbot(config={
            "email": config.openai.email,
            "password": config.openai.password,
            "proxy": config.openai.proxy,
            "paid": config.openai.paid
        })
    else:
        bot = Chatbot(config={
            "email": config.openai.email,
            "password": config.openai.password,
            "paid": config.openai.paid
        })


class ChatSession:
    conversation_id: str
    base_prompt: str = '你是 ChatGPT，一个大型语言模型。请以对话方式回复。\n\n\n'
    lock: asyncio.Lock

    def __init__(self, conversation_id):
        self.conversation_id = conversation_id
        self.lock = asyncio.Lock()

    def get_chat_response(self, message) -> str:
        with self.lock:
            os.environ.setdefault('BASE_PROMPT', self.base_prompt)
            result = ''
            for data in bot.ask(message, conversation_id=self.conversation_id):
                result = result + data["message"]
            return result


__sessions = {}


def get_chat_session(conversation_id: str) -> ChatSession:
    if conversation_id not in __sessions:
        __sessions[conversation_id] = ChatSession(conversation_id)
    return __sessions[conversation_id]
