from graia.ariadne.app import Ariadne
from graia.ariadne.model import Friend, Group
from graia.ariadne.message import Source
from typing import Union, Any, Dict, Tuple
from config import Config, OpenAIAuths
from loguru import logger
import os
import asyncio
import uuid
from time import sleep
from selenium.common.exceptions import TimeoutException
from manager import BotManager, BotInfo

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

    def __init__(self, session_id):
        self.session_id = session_id
        self.reset_conversation()

    async def load_conversation(self, keyword='default'):
        if not keyword in config.presets.keywords:
            if keyword == 'default':
                self.reset_conversation()
            else:
                raise ValueError("预设不存在，请检查你的输入是否有问题！")
        else:
            self.reset_conversation()
            presets = config.load_preset(keyword)
            for text in presets:
                if text.startswith('ChatGPT:'):
                    yield text.split('ChatGPT:')[-1].strip()
                elif text.startswith('User:'):
                    await self.get_chat_response(text.split('User:')[-1].strip())
                else:
                    await self.get_chat_response(text.split('User:')[-1].strip())
    def reset_conversation(self):
        if self.chatbot and self.chatbot.account.auto_remove_old_conversations and self.chatbot and self.conversation_id:
            self.chatbot.bot.delete_conversation(self.conversation_id)
        self.conversation_id = None
        self.parent_id = None
        self.prev_conversation_id = []
        self.prev_parent_id = []
        self.chatbot = botManager.pick()

    def rollback_conversation(self) -> bool:
        if len(self.prev_parent_id) <= 0:
            return False
        self.conversation_id = self.prev_conversation_id.pop()
        self.parent_id = self.prev_parent_id.pop()
        return True

    async def get_chat_response(self, message) -> str:
        self.prev_conversation_id.append(self.conversation_id)
        self.prev_parent_id.append(self.parent_id)

        bot = self.chatbot.bot
        bot.conversation_id = self.conversation_id
        bot.parent_id = self.parent_id

        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, self.chatbot.ask, message, self.conversation_id, self.parent_id)

        if self.conversation_id is None and self.chatbot.account.title_pattern:
            self.chatbot.bot.change_title(resp["conversation_id"], self.chatbot.account.title_pattern.format(session_id=self.session_id))

        self.conversation_id = resp["conversation_id"]
        self.parent_id = resp["parent_id"]

        return resp["message"]

__sessions = {}

def get_chat_session(id: str) -> ChatSession:
    if id not in __sessions:
        __sessions[id] = ChatSession(id)
    return __sessions[id]

import atexit
from rich.progress import Progress

def conversation_remover():
    with Progress() as progress:
        task = progress.add_task("[green]清理会话中", total=len(__sessions.values()))
        for session in __sessions.values():
            if session.chatbot.account.auto_remove_old_conversations and session.chatbot and session.conversation_id:
                try:
                    session.chatbot.bot.delete_conversation(session.conversation_id)
                except Exception as e:
                    logger.error(f"删除会话 {session.conversation_id} 失败：{str(e)}")
                finally:
                    progress.update(task, advance=1)
atexit.register(conversation_remover)