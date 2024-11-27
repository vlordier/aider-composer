from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ChatSetting:
    provider: str
    api_key: str
    model: str
    base_url: Optional[str] = None


@dataclass
class ChatSessionReference:
    readonly: bool
    fs_path: str


@dataclass
class ChatSessionData:
    chat_type: str
    diff_format: str
    message: str
    reference_list: List[ChatSessionReference]


@dataclass
class ChatChunkData:
    # event: data, usage, write, end, error, reflected, log
    # data: yield chunk message
    # usage: yield usage report
    # write: yield write files
    # end: end of chat
    # error: yield error message
    # reflected: yield reflected message
    # log: yield log message
    event: str
    data: Optional[dict] = None
