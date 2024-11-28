from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ChatSetting:
    """Settings for configuring the chat model/provider

    provider: The AI provider (e.g. openai, anthropic)
    api_key: Authentication key for the provider's API
    model: Name of the specific model to use
    base_url: Optional custom API endpoint URL
    """

    provider: str
    api_key: str
    model: str
    base_url: Optional[str] = None


@dataclass
class ChatSessionReference:
    """Reference to a file involved in the chat session

    readonly: Whether the file can be modified
    fs_path: Filesystem path to the referenced file
    """

    readonly: bool
    fs_path: str


@dataclass
class ChatSessionData:
    """Data for a chat session

    chat_type: Type of chat interaction ('ask' or 'code')
    diff_format: Format for showing diffs
    message: The user's chat message
    reference_list: List of files referenced in this chat
    """

    chat_type: str
    diff_format: str
    message: str
    reference_list: List[ChatSessionReference]


@dataclass
class ChatChunkData:
    """Data chunks sent during chat interactions

    Events:
    - data: Regular message chunk
    - usage: Model usage statistics
    - write: File write operations
    - end: Chat completion
    - error: Error messages
    - reflected: AI reflection messages
    - log: Debug log messages

    Args:
        event: Type of chat event
        data: Optional payload for the event
    """

    event: str
    data: Optional[dict] = None
