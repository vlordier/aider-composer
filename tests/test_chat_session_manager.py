import os
from unittest.mock import MagicMock, patch

import pytest

from server.chat_session_manager import CaptureIO, ChatSessionManager, ChatSetting
from server.models import ChatSessionData


@pytest.fixture()
def capture_io():
    return CaptureIO(pretty=False, yes=False)


@pytest.fixture()
def mock_coder():
    mock = MagicMock()
    mock.yield_stream = True
    mock.stream = True
    mock.pretty = False
    mock.reflected_message = None
    mock.usage_report = None
    mock.edit_format = "ask"
    mock.create.return_value = mock
    return mock


# Constants for test expectations
EXPECTED_CHAT_CHUNKS = 3  # 2 data chunks + 1 end chunk
EXPECTED_ERROR_CHUNKS = 2  # 1 error chunk + 1 end chunk


@pytest.fixture()
def chat_manager(mock_coder):
    with patch("server.chat_session_manager.Coder") as mock_coder_class:
        mock_coder_class.create.return_value = mock_coder
        return ChatSessionManager()


# Tests for ChatSessionManager
def test_chat_manager_initialization(chat_manager):
    assert chat_manager.chat_type == "ask"
    assert chat_manager.diff_format == "diff"
    assert chat_manager.reference_list == []


def test_update_model_openai(chat_manager):
    setting = ChatSetting(
        provider="openai", model="gpt-4", api_key="test-key", base_url=None
    )
    with patch.dict("os.environ", {}, clear=True):
        chat_manager.update_model(setting)
        assert "OPENAI_API_KEY" in os.environ
        assert os.environ["OPENAI_API_KEY"] == "test-key"


def test_update_model_ollama(chat_manager):
    setting = ChatSetting(
        provider="ollama",
        model="llama2",
        base_url="http://localhost:11434",
        api_key=None,  # Required but can be None for ollama
    )
    with patch.dict("os.environ", {}, clear=True):
        chat_manager.update_model(setting)
        assert "OLLAMA_API_BASE" in os.environ
        assert os.environ["OLLAMA_API_BASE"] == "http://localhost:11434"


def test_chat_basic_message(chat_manager, mock_coder):
    mock_coder.run_stream.return_value = ["Hello", "World"]
    mock_coder.io.get_captured_error_lines.return_value = []  # Mock empty error lines
    data = ChatSessionData(
        message="test message", chat_type="ask", diff_format="diff", reference_list=[]
    )

    chunks = list(chat_manager.chat(data))
    assert len(chunks) == EXPECTED_CHAT_CHUNKS  # 2 data chunks + 1 end chunk
    assert chunks[0].event == "data"
    assert chunks[0].data["chunk"] == "Hello"
    assert chunks[1].event == "data"
    assert chunks[1].data["chunk"] == "World"
    assert chunks[2].event == "end"


def test_chat_with_error(chat_manager, mock_coder):
    mock_coder.run_stream.side_effect = RuntimeError("Test error")
    data = ChatSessionData(
        message="test message", chat_type="ask", diff_format="diff", reference_list=[]
    )

    chunks = list(chat_manager.chat(data))
    assert len(chunks) == EXPECTED_ERROR_CHUNKS  # 1 error chunk + 1 end chunk
    assert chunks[0].event == "error"
    assert chunks[0].data["error"] == "Test error"
    assert chunks[1].event == "end"


def test_confirm_ask_reply(chat_manager):
    # Test that confirm_ask_reply sets the event
    chat_manager.confirm_ask_event.clear()
    chat_manager.confirm_ask_reply()
    assert chat_manager.confirm_ask_event.is_set()
