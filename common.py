from enum import Enum
from datetime import datetime
import json

class MessageType(Enum):
    RunTask = "run_task"
    Interrupt = "interrupt"

def timestamp():
    return datetime.strftime(datetime.now(), "%Y-%m-%d_%H:%M:%S.%f")


def format_message(action = None, data = None, msg = "ok"):
    message = {
        "action": action,
        "data": data,
        "msg": msg
    }
    return json.dumps(message)