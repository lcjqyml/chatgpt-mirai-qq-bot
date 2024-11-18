from typing import List

from g4f.client import Client
from g4f.Provider import *
from loguru import logger

from adapter.common.chat_helper import ChatMessage, ROLE_USER
from config import G4fModels


def convert_providers(providers: List[str]):
    ps = []
    for p in providers:
        ps.append(eval(p))
    return ps


def g4f_check_account(account: G4fModels):

    try:
        providers = []
        if account.providers:
            providers = convert_providers(account.providers)
        client = Client()
        response = client.chat.completions.create(
            model=account.model,
            provider=None if not providers else RetryProvider(providers),
            messages=[vars(ChatMessage(ROLE_USER, "hello"))],
        ).choices[0].message.content
        if not response or "error" in response.lower():
            return False
        logger.debug(f"g4f model ({vars(account)}) is active. hello -> {response}")
    except KeyError as e:
        logger.debug(f"g4f model ({vars(account)}) is inactive. hello -> {e}")
        return False
    return True


def parse(model_alias: str):
    from constants import botManager
    return next(
        (
            account
            for account in botManager.bots["gpt4free"]
            if model_alias == account.alias
        ),
        None
    )
