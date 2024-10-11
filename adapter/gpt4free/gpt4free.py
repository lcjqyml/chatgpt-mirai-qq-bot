from typing import Generator

from g4f.client import Client
from g4f.Provider import *

from adapter.botservice import BotAdapter
from adapter.common.chat_helper import ChatMessage, ROLE_ASSISTANT, ROLE_USER
from config import G4fModels
from constants import botManager
from adapter.gpt4free.g4f_helper import convert_providers


class Gpt4FreeAdapter(BotAdapter):
    """实例"""

    def __init__(self, session_id: str = "unknown", account: G4fModels = None):
        super().__init__(session_id)
        self.session_id = session_id
        self.account = account or botManager.pick("gpt4free")
        ps = convert_providers(account.providers)
        self.g4f_client = Client(
            provider=None if not ps else RetryProvider(ps)
        )
        self.conversation_history = []

    async def rollback(self):
        if len(self.conversation_history) <= 0:
            return False
        self.conversation_history = self.conversation_history[:-1]
        return True

    async def on_reset(self):
        self.conversation_history = []

    async def ask(self, prompt: str) -> Generator[str, None, None]:
        self.conversation_history.append(vars(ChatMessage(ROLE_USER, prompt)))
        response = self.g4f_client.chat.completions.create(
            model=self.account.model,
            messages=self.conversation_history,
        ).choices[0].message.content
        self.conversation_history.append(vars(ChatMessage(ROLE_ASSISTANT, response)))
        yield response
