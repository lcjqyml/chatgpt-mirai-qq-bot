import ctypes
from typing import Generator

from adapter.botservice import BotAdapter
import json
from urllib.parse import quote
from exceptions import BotOperationNotSupportedException
from config import BardCookiePath
from constants import botManager
from loguru import logger
import httpx
from utils.file_logger import write_log

hashu = lambda word: ctypes.c_uint64(hash(word)).value


class BardAdapter(BotAdapter):
    account: BardCookiePath

    def __init__(self, session_id: str = ""):
        super().__init__(session_id)
        self.at = None
        self.session_id = session_id
        self.account = botManager.pick('bard-cookie')
        self.client = httpx.AsyncClient(proxies=self.account.proxy)
        self.bard_session_id = ""
        self.r = ""
        self.rc = ""
        self.at = self.account.at
        self.headers = {
            "cookie": self.account.cookie_content,
            'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
        }

    async def get_at_token(self):
        if self.at:
            logger.info(f"SNlM0e: {self.at}")
            return
        response = await self.client.get(
            "https://gemini.google.com/?hl=en",
            timeout=30,
            headers=self.headers,
            follow_redirects=True,
        )
        response_text = response.text
        write_log(response_text)
        self.at = quote(response_text.split('"SNlM0e":"')[1].split('",')[0])

    async def rollback(self):
        raise BotOperationNotSupportedException()

    async def on_reset(self):
        await self.client.aclose()
        self.client = httpx.AsyncClient(proxies=self.account.proxy)
        self.bard_session_id = ""
        self.r = ""
        self.rc = ""
        await self.get_at_token()

    async def ask(self, prompt: str) -> Generator[str, None, None]:
        if not self.at:
            await self.get_at_token()
        try:
            url = "https://gemini.google.com/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate"
            content = quote(prompt.replace('"',"'")).replace("%0A","%5C%5Cn")
            # 奇怪的格式 [null,"[[\"\"],null,[\"\",\"\",\"\"]]"]
            raw_data = f"f.req=%5Bnull%2C%22%5B%5B%5C%22{content}%5C%22%5D%2Cnull%2C%5B%5C%22{self.bard_session_id}%5C%22%2C%5C%22{self.r}%5C%22%2C%5C%22{self.rc}%5C%22%5D%5D%22%5D&at={self.at}&"
            response = await self.client.post(
                url,
                timeout=30,
                headers=self.headers,
                content=raw_data,
            )
            if response.status_code != 200:
                logger.error(f"[Bard] 请求出现错误，状态码: {response.status_code}")
                logger.error(f"[Bard] {response.text}")
                raise Exception("Authentication failed")
            res_text = response.text
            write_log(res_text)
            res = res_text.split("\n")
            for lines in res:
                if "wrb.fr" in lines:
                    data = json.loads(json.loads(lines)[0][2])
                    result = data[4][0][1][0]
                    self.bard_session_id = data[1][0]
                    self.r = data[1][1]  # 用于下一次请求, 这个位置是固定的
                    # self.rc = data[4][1][0]
                    for check in data:
                        if not check:
                            continue
                        try:
                            for element in [element for row in check for element in row]:
                                if "rc_" in element:
                                    self.rc = element
                                    break
                        except:
                            continue
                    logger.debug(f"[Bard] {self.bard_session_id} - {self.r} - {self.rc} - {result}")
                    yield result
                    break

        except Exception as e:
            logger.exception(e)
            yield "[Bard] 出现了些错误"
            await self.on_reset()
            return
