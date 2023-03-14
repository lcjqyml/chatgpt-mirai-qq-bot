import asyncio
import hashlib
import itertools
import os
import sys
import time
from datetime import datetime
from typing import Union, List

import OpenAIAuth
import urllib3.exceptions
from loguru import logger
from requests.exceptions import SSLError
from revChatGPT.V1 import Chatbot as V1Chatbot, Error as V1Error
from revChatGPT.V3 import Chatbot as V3Chatbot
from tinydb import TinyDB, Query

import utils.network as network
from config import Config
from config import OpenAIAuthBase, OpenAIEmailAuth, OpenAISessionTokenAuth, OpenAIAccessTokenAuth, OpenAIAPIKey
from pojo.Constants import Constants

sys.path.append(os.getcwd())

config = Config.load_config()


class BotInfo(asyncio.Lock):
    id = 0

    account: OpenAIAuthBase

    bot: Union[V1Chatbot, V3Chatbot]

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
                self.bot.delete_conversation(convo_id)
        elif isinstance(self.bot, V3Chatbot):
            if no_system_prompt:
                system_prompt = "."
            else:
                system_prompt = self.account.system_prompt.format(current_date=datetime.now().strftime('%Y-%m-%d'))
            self.bot.reset(convo_id=convo_id, system_prompt=system_prompt)

    def __init__(self, bot, api_version):
        self.bot = bot
        self.api_version = api_version
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
    """Bot list"""

    accounts: List[Union[OpenAIEmailAuth, OpenAISessionTokenAuth, OpenAIAccessTokenAuth, OpenAIAPIKey]]
    """Account infos"""

    roundrobin: itertools.cycle = None

    def __init__(self, accounts: List[Union[OpenAIEmailAuth, OpenAISessionTokenAuth, OpenAIAccessTokenAuth, OpenAIAPIKey]]) -> None:
        self.accounts = accounts
        try:
            os.mkdir('data')
            logger.warning(
                "警告：未检测到 data 目录，如果你通过 Docker 部署，请挂载此目录以实现登录缓存，否则可忽略此消息。")
        except:
            pass
        self.cache_db = TinyDB('data/login_caches.json')

    def login(self):
        for i, account in enumerate(self.accounts):
            logger.info("正在登录第 {i} 个 OpenAI 账号", i=i + 1)
            try:
                if account.api_version == "V1":
                    bot = self.__login_v1(account)
                    bot.id = i
                    bot.account = account
                    self.v1bots.append(bot)
                    logger.success("V1账号登录成功！")
                elif account.api_version == "V3":
                    bot = self.__login_v3(account)
                    bot.id = i
                    bot.account = account
                    self.v3bots.append(bot)
                    logger.success("V3账号登录成功！")
                else:
                    raise Exception("未定义的登录接口版本：" + account.api_version)
                self.bots.append(bot)
                logger.debug("等待 8 秒……")
                time.sleep(8)
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

    def __save_login_cache(self, account: OpenAIAuthBase, cache: dict):
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

        # 我承认这部分代码有点蠢
        def __v1_check_auth(bot) -> bool:
            try:
                bot.get_conversations(0, 1)
                return True
            except (V1Error, KeyError) as e:
                return False

        def get_access_token(bot: V1Chatbot):
            return bot.session.headers.get('Authorization').removeprefix('Bearer ')

        if 'access_token' in cached_account:
            logger.info("尝试使用 access_token 登录中...")
            login_config['access_token'] = cached_account['access_token']
            bot = V1Chatbot(config=login_config)
            if __v1_check_auth(bot):
                return BotInfo(bot, account.api_version)

        if 'session_token' in cached_account:
            logger.info("尝试使用 session_token 登录中...")
            login_config.pop('access_token', None)
            login_config['session_token'] = cached_account['session_token']
            bot = V1Chatbot(config=login_config)
            self.__save_login_cache(account=account, cache={
                "session_token": login_config['session_token'],
                "access_token": get_access_token(bot),
            })
            if __v1_check_auth(bot):
                return BotInfo(bot, account.api_version)

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
            if __v1_check_auth(bot):
                return BotInfo(bot, account.api_version)
        # Invalidate cache
        self.__save_login_cache(account=account, cache={})
        raise Exception("All login method failed")

    def __login_v3(self, account: OpenAIAuthBase) -> BotInfo:
        cached_account = dict(self.__load_login_cache(account), **account.dict())
        login_config = self.__check_proxy_config(account)

        def __v3_check_auth(bot) -> bool:
            try:
                bot.ask("ping")
                return True
            except KeyError as e:
                return False

        if 'api_key' in cached_account:
            bot = V3Chatbot(api_key=cached_account['api_key'],
                            proxy=login_config.get('proxy', None),
                            engine=cached_account['chat_model'],
                            temperature=cached_account['temperature'],
                            system_prompt=".",
                            max_tokens=Constants.MAX_TOKENS.value)
            if __v3_check_auth(bot):
                return BotInfo(bot, account.api_version)
        # Invalidate cache
        self.__save_login_cache(account=account, cache={})
        raise Exception("All login method failed")

    @staticmethod
    def __check_proxy_config(account: OpenAIAuthBase) -> dict:
        login_config = dict()
        if account.proxy is not None:
            logger.info(f"正在检查代理配置：{account.proxy}")
            from urllib.parse import urlparse
            proxy_addr = urlparse(account.proxy)
            if not network.is_open(proxy_addr.hostname, proxy_addr.port):
                raise Exception("failed to connect to the proxy server")
            login_config['proxy'] = account.proxy
        return login_config

    def pick(self, api_version) -> BotInfo:
        if api_version == "V1":
            self.roundrobin = itertools.cycle(self.v1bots)
        elif api_version == "V2":
            self.roundrobin = itertools.cycle(self.v2bots)
        elif api_version == "V3":
            self.roundrobin = itertools.cycle(self.v3bots)
        else:
            self.roundrobin = itertools.cycle(self.bots)
        return next(self.roundrobin)
