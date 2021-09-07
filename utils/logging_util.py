"""
Add Context logging functionality
"""
import logging
from typing import Tuple, Union
from telegram import Update
from dataclasses import dataclass

@dataclass
class ContextInfo:
    chat_id: str
    chat_title: str
    message_id: int 
    message_text: str

class ContextAdapter(logging.LoggerAdapter):
    def process(self, message: str, kwargs) -> Tuple[str, dict]:
        e: ContextInfo = self.extra

        chat_info = f'[{e.chat_title} ({e.chat_id})]'
        message_info = f'@message<{e.message_id}>: "{e.message_text}"'
        
        return  f'{chat_info} {message} {message_info}', kwargs


def bind_logger(update: Update, name: str=None) -> Union[logging.Logger, logging.LoggerAdapter]:
    logger = logging.getLogger(name)
    try:    
        context_info = ContextInfo(
            chat_id=update.effective_message.chat.id,
            chat_title=update.effective_message.chat.title if update.effective_message.chat.type != 'private' else f"@{update.effective_message.chat.username} ({update.effective_message.chat.last_name}, {update.effective_message.chat.first_name})",
            message_id=update.effective_message.message_id,
            message_text=update.effective_message.text
        )
    except KeyError as e:
        logging.warning(f'Failed to generate ContextInfo: {e.message}')
        return logger

    return ContextAdapter(logger, context_info)
