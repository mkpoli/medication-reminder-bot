import json
import logging
logger = logging.getLogger()

from utils.logging_util import bind_logger

from distutils.util import strtobool
from telegram import Update, Message
from telegram.ext import CallbackContext, Dispatcher
from typing import Any, Callable, Optional, Sequence, Tuple, TypeVar

class BadUsage(ValueError):
    pass

NEWLINE = '\n'

class Parameter: 
    def __init__(self, name: str, type: type, desc: str, checker: Optional[Callable]=None, optional: bool=False) -> None:
        self.name = name
        self.type = type
        self.desc = desc
        self.checker = checker
        self.optional = optional

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        return f"Parameter({self.name})"
    
    def __repr__(self) -> str:
        return f"Parameter({self.name}, {self.type}, {self.desc})"

class Command:
    def __init__(self, name: str, handler: Callable, description: str, parameters: Sequence[Parameter], last_ignore_space: bool=False) -> None:
        self.name = name
        self.handler = handler
        self.description = description
        self.parameters = parameters
        self.last_ignore_space = last_ignore_space
        
    def __str__(self) -> str:
        return f"Command({self.name}, {self.description})"
    
    def print_usage(self, update: Update, delete_after_secs: int=0) -> None:
        do_command_usage = lambda: command_usage(self.name, self.parameters, self.description, update.effective_message)
        if delete_after_secs:
            delete_after(delete_after_secs)(do_command_usage())
        else:
            do_command_usage()
    
    def get_handler(self) -> Callable:
        def handler(update: Update, context: CallbackContext):
            try:
                args = parse_command(self.parameters, self.description, update, self.last_ignore_space)
            except BadUsage as e:
                self.print_usage(update, 10)
                bind_logger(update, __name__).debug(f'BadUsage: {e}')
                return
            return self.handler(update, context, self, args)
        return handler
    

def parse_command(parameters: Sequence[Parameter], description: str, update: Update, last_ignore_space=False) -> Tuple[str, dict]:
    required_parameters = list(filter(lambda x: not x.optional, parameters))

    if last_ignore_space and len(required_parameters) != len(parameters):
        raise IndexError("Optional parameters cannot co-exist with last_ignore_space=True !")

    command_parts = update.effective_message.text.split()
    command, args = command_parts[0], command_parts[1:]
    if last_ignore_space:
        args = update.effective_message.text.split(maxsplit = len(parameters))[1:]

    bind_logger(update, __name__).debug(f"command={command}, args={','.join(args)}")

    if len(args) < len(required_parameters):
        raise BadUsage('args less than required')

    if not last_ignore_space and len(args) > len(parameters):
        raise BadUsage('over argument')

    TYPE_CONVERSION = {
        int: int,
        float: float,
        bool: lambda x: bool(strtobool(x))
    }

    result = {}

    for i, param in enumerate(parameters):
        try:
            arg = args[i]
        except IndexError:
            break
        
        if param.type in TYPE_CONVERSION:
            try:
                arg = TYPE_CONVERSION[param.type](arg)
            except ValueError:
                raise BadUsage('bad value of type')
                
        if param.checker and not param.checker(arg):
            raise BadUsage('failed check')

        result[param.name] = arg

    return result

import time

def _delete_after(delay: int, message: Message):
    """Delete message after specified seconds.

    Args:
        delay (int): Delay in secs
        message (Message): Message to delete
    """
    time.sleep(delay)
    message.delete()
    logger.debug(f'Message {message.message_id} in {message.chat.type} chat {message.chat.id} deleted:\n{message.text}')
    return

RT = TypeVar('RT')
def delete_after(delay: int) -> Callable[[Callable[..., Message]], Callable[..., None]]:
    def decorator(func: Callable[..., Message]) -> Callable[..., None]:
        def wrapper(*args, **kwargs) -> None:
            sent_message = func(*args, **kwargs)
            if not isinstance(sent_message, Message):
                raise TypeError('Message sender is not returning sent message')
            dispatcher = Dispatcher.get_instance()
            dispatcher.run_async(_delete_after, delay, sent_message)
        return wrapper
    return decorator

# @delete_after(10)
def command_usage(command: str, parameters: list[Parameter], description: str, reply_to: Message) -> Message: 
    """Reply to user when a bad command usage is found.

    Args:
        command (str): Command Name
        parameters (Sequence[Parameter]): Parameters of Command
        description (str): Description of Command
        reply_to (Message): User Message of Bad Usage
    """
    command_repr = f"/{command} {' '.join(f'???{param.name}???' for param in parameters)}"
    if parameters:
        max_length = max(len(param.name) for param in parameters)
        paramtr_desc = "\n".join(f"    <code>{param.name.rjust(max_length)}</code> - {param.desc} " for param in parameters)
    else:
        paramtr_desc = "??????????????????"
    sent_message = reply_to.reply_text(
        f"<b>?????????????????????</b>\n<code>{ command_repr }</code>\n\n{ description }\n{ paramtr_desc }")
    
    return sent_message

MAX_MESSAGE_TXT_LENGTH = 4096
RESERVE_SPACE = 10

def page_message(update: Update, context: CallbackContext, text: str, reply: bool=False) -> Sequence[Message]:
    chat_id = update.effective_message.chat_id

    def send(text):
        if reply:
            return update.effective_message.reply_text(text=text)
        else:
            return context.bot.send_message(chat_id=chat_id, text=text)

    if len(text) < MAX_MESSAGE_TXT_LENGTH:
        return [send(text=text)]

    page_length = MAX_MESSAGE_TXT_LENGTH - RESERVE_SPACE
    parts = [text[i:i + page_length] for i in range(0, len(text), page_length)]
    # we are reserving 8 characters for adding the page number in
    # the following format: [01/10]

    parts = [f"[{i + 1}/{len(parts)}] \n{part}" for i, part in enumerate(parts)]

    bind_logger(update, __name__).debug(f"Sending message in {len(parts)} pages")
    
    messages = []
    for part in parts:
        messages.append(send(text=part))
    return messages

def reply(update: Update, context: CallbackContext, text: str) -> None:
    bind_logger(update, __name__).debug(f"Replying '{text}'")
    if update.effective_message:
        update.effective_message.reply_text(text=text)
    else:
        return context.bot.send_message(chat_id=context. update.effective_chat.id, text=text)

# Dump all data command
def dumpall(update: Update, context: CallbackContext, command: Command, args: Sequence[Any]) -> None:
    datae = {
        "Chat Data": context.chat_data,
        "User Data": context.user_data,
         "Bot Data": context.bot_data
    }
    content = '\n\n'.join(f'<b>{k}</b><pre><code class="language-json">{json.dumps(v, indent=2, ensure_ascii=False, sort_keys=True)}</code></pre>' for k, v in datae.items())
    page_message(
        update, context,
        content, reply=True
    )
