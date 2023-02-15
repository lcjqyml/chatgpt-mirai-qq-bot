import asyncio
import os

from loguru import logger
from revChatGPT.V1 import Chatbot

from config import Config

config = Config.load_config()

os.environ.setdefault('TEMPERATURE', str(config.openai.temperature))

bot = None


def get_auth_config():
    auth_config = {}
    if config.openai.email and config.openai.password:
        auth_config["email"] = config.openai.email
        auth_config["password"] = config.openai.password
    if config.openai.proxy:
        auth_config["proxy"] = config.openai.proxy
    if config.openai.paid:
        auth_config["paid"] = config.openai.paid
    if config.openai.session_token:
        auth_config["session_token"] = config.openai.session_token
    if config.openai.access_token:
        auth_config["access_token"] = config.openai.access_token
    return auth_config


def setup():
    global bot
    if not (config.openai.email and config.openai.password) and not config.openai.access_token:
        logger.error("配置文件出错！请配置 OpenAI 的邮箱、密码或者access_token。")
        exit(-1)
    bot = Chatbot(config=get_auth_config())


class ChatSession:
    conversation_id: str
    base_prompt: str = '你是 ChatGPT，一个大型语言模型。请以对话方式回复。\n\n\n'

    def __init__(self, conversation_id):
        self.conversation_id = conversation_id

    def get_chat_response(self, message) -> str:
        os.environ.setdefault('BASE_PROMPT', self.base_prompt)
        result = ""
        prev_text = ""
        for data in bot.ask(message, conversation_id=self.conversation_id):
            response_text = data["message"][len(prev_text):]
            result = result + response_text
            prev_text = data["message"]
        return result


__sessions = {}


def get_chat_session(conversation_id: str) -> ChatSession:
    if conversation_id not in __sessions:
        __sessions[conversation_id] = ChatSession(conversation_id)
    return __sessions[conversation_id]
