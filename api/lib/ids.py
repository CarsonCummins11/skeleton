import random
import string
from enum import Enum
from typing import Any


class IdType(Enum):
    USER = 1
    ITEM = 2
    # Add more types here as your domain grows


ID_SAMPLE_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def id_type_as_char(t: IdType) -> str:
    return ID_SAMPLE_CHARS[t.value]


def id_type_from_id(id: str) -> IdType:
    type_char = id[0]
    if type_char not in ID_SAMPLE_CHARS:
        raise ValueError(f"Invalid ID type character: {type_char}")
    type_index = ID_SAMPLE_CHARS.index(type_char)
    return IdType(type_index)


def generate_id(t: IdType) -> str:
    noise = "".join(random.choices(string.ascii_letters + string.digits, k=11))
    new_id = id_type_as_char(t) + noise
    if not is_id_of_type(new_id, t):
        raise ValueError(f"Generated ID {new_id} is not of type {t}")
    return new_id


def is_id_of_type(id: Any, t: IdType) -> bool:
    if not isinstance(id, str):
        return False
    if len(id) != 12:
        return False
    return id_type_from_id(id) == t
