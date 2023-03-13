import os
import sys

from loguru import logger
from requests.exceptions import SSLError

import chatbot
from config import Config
from pojo.Constants import InteractiveMode

sys.path.append(os.getcwd())

config = Config.load_config()


async def handle_message(session_id: str, message: str, api_version: str = None) -> str:
    if not message.strip():
        return config.response.placeholder

    session = chatbot.get_chat_session(session_id, api_version)

    # ping
    if message.strip() in config.trigger.ping_command:
        return session.get_status()

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
                if session.is_chat_mode():
                    return config.response.reset_chat
                elif session.is_qa_mode():
                    return config.response.reset_qa
                else:
                    return config.response.reset
            # 聊天模式
            if message.strip() in config.trigger.chat_command:
                session.reset_conversation(interactive_mode=InteractiveMode.CHAT)
                return config.response.reset_chat
            # qa模式
            if message.strip() in config.trigger.chat_command:
                session.reset_conversation(interactive_mode=InteractiveMode.Q_A)
                return config.response.reset_qa
            # 正常交流
            resp = await session.get_chat_response(message)
            interactive_mode_info = "[" + session.interactive_mode.value + "]: " if session.interactive_mode else ""
            if resp:
                logger.debug(f"API[{session.api_version}] - {interactive_mode_info}{session_id} - {resp}")
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
