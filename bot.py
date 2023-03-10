import os
import sys

from loguru import logger
from requests.exceptions import SSLError

import chatbot
from config import Config

sys.path.append(os.getcwd())

config = Config.load_config()


async def handle_message(session_id: str, message: str) -> str:
    if not message.strip():
        return config.response.placeholder

    session, is_new_session = chatbot.get_chat_session(session_id)

    # 回滚
    if message.strip() in config.trigger.rollback_command:
        resp = session.rollback_conversation()
        if resp:
            return config.response.rollback_success
        return config.response.rollback_fail

    # 队列满时拒绝新的消息
    if 0 < config.response.max_queue_size < session.chatbot.queue_size:
        return config.response.queue_full

    # 以下开始需要排队
    async with session.chatbot:
        try:
            # 重置会话
            if message.strip() in config.trigger.reset_command:
                session.reset_conversation()
                return config.response.reset
            # 正常交流
            resp = await session.get_chat_response(message)
            if resp:
                logger.debug(f"{session_id} - {session.chatbot.id} {resp}")
                return resp.strip()
        except SSLError as e:
            logger.exception(e)
            return config.response.error_network_failure.format(exc=e)
        except Exception as e:
            # Other un-handled exceptions
            if 'Too many requests' in str(e):
                return config.response.error_request_too_many.format(exc=e)
            elif 'overloaded' in str(e):
                return config.response.error_server_overloaded.format(exc=e)
            elif 'Unauthorized' in str(e):
                return config.response.error_session_authenciate_failed.format(exc=e)
            logger.exception(e)
            return config.response.error_format.format(exc=e)
    # 排队结束
