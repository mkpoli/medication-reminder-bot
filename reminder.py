from dataclasses import dataclass
from typing import List

from mashumaro import DataClassDictMixin
from telegram.ext import CallbackContext

@dataclass(unsafe_hash=True)
class Medication(DataClassDictMixin):
    name: str
    amount: str
    
    def __str__(self) -> str:
        return f"{self.name} {self.amount}"

@dataclass
class Remindee(DataClassDictMixin):
    nickname: str
    medications: List[Medication]
    chat_id: int
    username: str=None

    def format_reminder_message(self):
        at_username = f'@{self.username} ' if self.username else ''
        return f"{at_username}{self.nickname}，您的 {'、'.join(str(med) for med in self.medications)} 已就位，请及时服用〜"

def append_remindee(user_id: int, remindee: Remindee, context: CallbackContext):
    if not context.bot_data.get('remindees'):
        context.bot_data['remindees'] = {}
    if remindee.username not in context.bot_data['remindees'].keys():
        context.bot_data['remindees'][user_id] = remindee.to_dict()

def get_remindee(user_id: str, context: CallbackContext) -> Remindee:
    if not context.bot_data.get('remindees'):
        context.bot_data['remindees'] = {}
    if not context.bot_data['remindees'].get(user_id):
        return None
    return Remindee.from_dict(context.bot_data['remindees'][user_id])

def delete_remindee(user_id: int, context: CallbackContext) -> Remindee:
    if (remindee := get_remindee(user_id, context)):
        del context.bot_data['remindees'][user_id]
    return remindee

def update_medications(user_id: int, medications: list[Medication], context: CallbackContext) -> Remindee:
    if not (remindee := get_remindee(user_id, context)):
        return None
    
    remindee.medications = medications
    context.bot_data['remindees'][user_id] = remindee.to_dict()
    return remindee

# TODO: update_nickname
def generate_remind(remindee: Remindee):
    def remind(context: CallbackContext) -> None:
        context.bot.send_message(
            chat_id=remindee.chat_id,
            text=remindee.format_reminder_message()
        )
    return remind
