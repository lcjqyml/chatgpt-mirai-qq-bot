import asyncio
import hashlib
import itertools
import json
import os
import sys
import threading
import time
from datetime import datetime
from typing import Union, List

import OpenAIAuth
import urllib3.exceptions
from loguru import logger
from requests.exceptions import SSLError
from revChatGPT.V1 import Chatbot as V1Chatbot, Error as V1Error
from revChatGPT.V3 import Chatbot as V3Chatbot
from poe import Client as PoeChatbot
from tinydb import TinyDB, Query

import utils.network as network
from config import Config, AuthBase
from config import OpenAIAuthBase, OpenAIEmailAuth, OpenAISessionTokenAuth, OpenAIAccessTokenAuth, OpenAIAPIKey, PoeAuth
from pojo.Constants import Constants

sys.path.append(os.getcwd())

config = Config.load_config()


class BotInfo(asyncio.Lock):
    id = 0

    account: AuthBase

    account_info = {}

    bot: Union[V1Chatbot, V3Chatbot, PoeChatbot]

    api_version: str

    queue_size: int = 0

    unused_conversations_pools = {}

    lastAccessed = None
    """Date when bot is accessed last time"""

    lastFailure = None
    """Date when bot encounter an error last time"""

    def reset(self, convo_id: str, no_system_prompt: bool = False):
        if isinstance(self.bot, V1Chatbot):
            if convo_id is not None:
                try:
                    self.bot.delete_conversation(convo_id)
                except V1Error as e:
                    logger.warning(f"Failed to delete conversation: {convo_id}")
        elif isinstance(self.bot, V3Chatbot):
            if no_system_prompt:
                system_prompt = "."
            else:
                system_prompt = self.account_info["system_prompt"].format(
                    current_date=datetime.now().strftime('%Y-%m-%d'))
            self.bot.reset(convo_id=convo_id, system_prompt=system_prompt)

    def is_running(self):
        return BotManager.check_auth(self.bot)

    def __init__(self, bot, api_version, account):
        self.bot = bot
        self.api_version = str(api_version).upper()
        self.account = account
        self.account_info = vars(account)
        super().__init__()

    def __str__(self) -> str:
        return self.bot.__str__()

    async def __aenter__(self) -> None:
        self.queue_size = self.queue_size + 1
        return await super().__aenter__()

    async def __aexit__(self, exc_type: type[BaseException], exc: BaseException, tb) -> None:
        self.queue_size = self.queue_size - 1
        return await super().__aexit__(exc_type, exc, tb)


class BotManager:
    """Bot lifecycle manager."""
    bots: List[BotInfo] = []
    v1bots: List[BotInfo] = []
    v2bots: List[BotInfo] = []
    v3bots: List[BotInfo] = []
    poe_bots: List[BotInfo] = []
    """Bot list"""

    accounts: List[Union[OpenAIEmailAuth, OpenAISessionTokenAuth, OpenAIAccessTokenAuth, OpenAIAPIKey, PoeAuth]]
    """Account infos"""

    roundrobin: itertools.cycle = None

    def __init__(self, accounts: List[Union[OpenAIEmailAuth, OpenAISessionTokenAuth,
                                            OpenAIAccessTokenAuth, OpenAIAPIKey, PoeAuth]]) -> None:
        self.accounts = accounts
        try:
            os.mkdir('data')
            logger.warning(
                "警告：未检测到 data 目录，如果你通过 Docker 部署，请挂载此目录以实现登录缓存，否则可忽略此消息。")
        except:
            pass
        self.cache_db = TinyDB('data/login_caches.json')
        self.lock = threading.Lock()

    def login(self):
        for i, account in enumerate(self.accounts):
            logger.info("正在登录第 {i} 个账号", i=i + 1)
            try:
                if account.is_openai_auth():
                    if account.api_version == Constants.V1_API.value:
                        bot = self.__login_v1(account)
                        bot.id = i
                        bot.account = account
                        self.v1bots.append(bot)
                        logger.success("V1账号登录成功！")
                    elif account.api_version == Constants.V3_API.value:
                        bot = self.__login_v3(account)
                        bot.id = i
                        bot.account = account
                        self.v3bots.append(bot)
                        logger.success("V3账号登录成功！")
                    else:
                        raise Exception("未定义的登录接口版本：" + account.api_version)
                elif account.is_poe_auth():
                    bot = self.__login_poe(account)
                    bot.id = i
                    bot.account = account
                    self.poe_bots.append(bot)
                    logger.success("poe账号登录成功！")
                else:
                    raise Exception("未定义的登录接口：" + json.dumps(account))
                self.bots.append(bot)
                logger.debug("等待 3 秒……")
                time.sleep(3)
            except OpenAIAuth.Error as e:
                logger.error("登录失败! 请检查 IP 、代理或者账号密码是否正确{exc}", exc=e)
            except (SSLError, urllib3.exceptions.MaxRetryError) as e:
                logger.error("登录失败! 连接 OpenAI 服务器失败,请检查网络和本地代理设置！{exc}", exc=e)
            except Exception as e:
                err_msg = str(e)
                if "failed to connect to the proxy server" in err_msg:
                    logger.error("登录失败! 无法连接至本地代理服务器，请检查配置文件中的 proxy 是否正确！{exc}", exc=e)
                elif "All login method failed" in err_msg:
                    logger.error("登录失败! 所有登录方法均已失效,请检查 IP、代理或者登录信息是否正确{exc}", exc=e)
                else:
                    logger.error("未知错误：")
                    logger.exception(e)
        if len(self.bots) < 1:
            logger.error("所有账号均登录失败，无法继续启动！")
            exit(-2)
        logger.success(f"成功登录 {len(self.bots)}/{len(self.accounts)} 个账号！")

    def __save_login_cache(self, account: AuthBase, cache: dict):
        """保存登录缓存"""
        account_sha = hashlib.sha256(account.json().encode('utf8')).hexdigest()
        q = Query()
        self.cache_db.upsert({'account': account_sha, 'cache': cache}, q.account == account_sha)

    def __load_login_cache(self, account):
        """读取登录缓存"""
        account_sha = hashlib.sha256(account.json().encode('utf8')).hexdigest()
        q = Query()
        cache = self.cache_db.get(q.account == account_sha)
        return cache['cache'] if cache is not None else dict()

    def __login_v1(self, account: OpenAIAuthBase) -> BotInfo:
        cached_account = dict(self.__load_login_cache(account), **account.dict())
        login_config = self.__check_proxy_config(account)

        def get_access_token(bot: V1Chatbot):
            return bot.session.headers.get('Authorization').removeprefix('Bearer ')

        if 'access_token' in cached_account:
            logger.info("尝试使用 access_token 登录中...")
            login_config['access_token'] = cached_account['access_token']
            bot = V1Chatbot(config=login_config)
            if BotManager.check_auth(bot):
                return BotInfo(bot, account.api_version, account)

        if 'session_token' in cached_account:
            logger.info("尝试使用 session_token 登录中...")
            login_config.pop('access_token', None)
            login_config['session_token'] = cached_account['session_token']
            bot = V1Chatbot(config=login_config)
            self.__save_login_cache(account=account, cache={
                "session_token": login_config['session_token'],
                "access_token": get_access_token(bot),
            })
            if BotManager.check_auth(bot):
                return BotInfo(bot, account.api_version, account)

        if 'password' in cached_account:
            logger.info("尝试使用 email + password 登录中...")
            login_config.pop('access_token', None)
            login_config.pop('session_token', None)
            login_config['email'] = cached_account['email']
            login_config['password'] = cached_account['password']
            bot = V1Chatbot(config=login_config)
            self.__save_login_cache(account=account, cache={
                "session_token": bot.config['session_token'],
                "access_token": get_access_token(bot)
            })
            if BotManager.check_auth(bot):
                return BotInfo(bot, account.api_version, account)
        # Invalidate cache
        self.__save_login_cache(account=account, cache={})
        raise Exception("All login method failed")

    def __login_v3(self, account: OpenAIAuthBase) -> BotInfo:
        cached_account = dict(self.__load_login_cache(account), **account.dict())
        login_config = BotManager.__check_proxy_config(account)

        if 'api_key' in cached_account:
            bot = V3Chatbot(api_key=cached_account['api_key'],
                            proxy=login_config.get('proxy', None),
                            engine=cached_account['chat_model'],
                            temperature=cached_account['temperature'],
                            system_prompt=".",
                            max_tokens=Constants.MAX_TOKENS.value)
            if BotManager.check_auth(bot):
                return BotInfo(bot, account.api_version, account)
        # Invalidate cache
        self.__save_login_cache(account=account, cache={})
        raise Exception("All login method failed")

    def __login_poe(self, account: PoeAuth) -> BotInfo:
        cached_account = dict(self.__load_login_cache(account), **account.dict())
        bot = PoeChatbot(cached_account["p_b_token"])
        if BotManager.check_auth(bot):
            return BotInfo(bot, account.api_version, account)
        # Invalidate cache
        self.__save_login_cache(account=account, cache={})
        raise Exception("All login method failed")

    @staticmethod
    def check_auth(bot: [V1Chatbot, V3Chatbot, PoeChatbot]):
        if isinstance(bot, V1Chatbot):
            return BotManager.v1_check_auth(bot)
        elif isinstance(bot, V3Chatbot):
            return BotManager.v3_check_auth(bot)
        elif isinstance(bot, PoeChatbot):
            return BotManager.poe_check_auth(bot)
        raise Exception(f"Unknown bot -> {str(bot)}")

    @staticmethod
    def poe_check_auth(bot: PoeChatbot) -> bool:
        try:
            response = bot.get_bot_names()
            logger.debug(f"poe bot is running. bot names -> {response}")
            return True
        except KeyError as e:
            return False

    @staticmethod
    def v3_check_auth(bot: V3Chatbot) -> bool:
        try:
            response = bot.ask("ping")
            logger.debug(f"v3 bot[{bot.api_key}] is running. ping -> {response}")
            return True
        except KeyError as e:
            return False

    @staticmethod
    def v1_check_auth(bot: V1Chatbot) -> bool:
        try:
            response = bot.get_conversations(0, 1)
            logger.debug(f"v1 bot is running. Top conversation -> {str(response)}")
            return True
        except (V1Error, KeyError) as e:
            return False

    @staticmethod
    def __check_proxy_config(account: AuthBase) -> dict:
        login_config = dict()
        if account.proxy is not None:
            logger.info(f"正在检查代理配置：{account.proxy}")
            from urllib.parse import urlparse
            proxy_addr = urlparse(account.proxy)
            if not network.is_open(proxy_addr.hostname, proxy_addr.port):
                raise Exception("failed to connect to the proxy server")
            login_config['proxy'] = account.proxy
        return login_config

    def check_bots(self, api_version: str = None):
        """检测bot是否有效，剔除无效bot, 若没有有效bot则返回False"""
        if api_version is None:
            self.bots = [bot for bot in self.bots if bot.is_running()]
            self.v1bots = [bot for bot in self.bots if bot.api_version == Constants.V1_API.value]
            self.v2bots = [bot for bot in self.bots if bot.api_version == Constants.V2_API.value]
            self.v3bots = [bot for bot in self.bots if bot.api_version == Constants.V3_API.value]
            self.poe_bots = [bot for bot in self.bots if bot.api_version == Constants.POE_API.value]
            if len(self.bots) == 0:
                return False
        elif api_version == Constants.V1_API.value:
            self.v1bots = [bot for bot in self.v1bots if bot.is_running()]
            self.bots = self.v1bots + self.v2bots + self.v3bots + self.poe_bots
            if len(self.v1bots) == 0:
                return False
        elif api_version == Constants.V2_API.value:
            self.v2bots = [bot for bot in self.v2bots if bot.is_running()]
            self.bots = self.v1bots + self.v2bots + self.v3bots + self.poe_bots
            if len(self.v2bots) == 0:
                return False
        elif api_version == Constants.V3_API.value:
            self.v3bots = [bot for bot in self.v3bots if bot.is_running()]
            self.bots = self.v1bots + self.v2bots + self.v3bots + self.poe_bots
            if len(self.v3bots) == 0:
                return False
        elif api_version == Constants.POE_API.value:
            self.poe_bots = [bot for bot in self.poe_bots if bot.is_running()]
            self.bots = self.v1bots + self.v2bots + self.v3bots + self.poe_bots
            if len(self.poe_bots) == 0:
                return False
        return True

    def pick(self, api_version) -> BotInfo:
        with self.lock:
            if api_version is None or not self.check_bots(api_version):
                return self.pick_any()
            if api_version == Constants.V1_API.value:
                self.roundrobin = itertools.cycle(self.v1bots)
            elif api_version == Constants.V2_API.value:
                self.roundrobin = itertools.cycle(self.v2bots)
            elif api_version == Constants.V3_API.value:
                self.roundrobin = itertools.cycle(self.v3bots)
            elif api_version == Constants.POE_API.value:
                self.roundrobin = itertools.cycle(self.poe_bots)
            return next(self.roundrobin)

    def pick_any(self) -> BotInfo:
        if not self.check_bots():
            raise Exception("No available bot.")
        self.roundrobin = itertools.cycle(self.bots)
        return next(self.roundrobin)

    @staticmethod
    def reset_poe_bot(chatbot: BotInfo) -> BotInfo:
        bot = PoeChatbot(chatbot.account_info["p_b_token"])
        if BotManager.check_auth(bot):
            chatbot.bot = bot
            return chatbot
        raise Exception("Can not reset bot!")
