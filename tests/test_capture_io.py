
import pytest
from server.chat_session_manager import CaptureIO

@pytest.fixture
def capture_io():
    return CaptureIO(pretty=False, yes=False)

def test_initialization(capture_io):
    assert capture_io.lines == []
    assert capture_io.error_lines == []
    assert capture_io.write_files == {}

def test_tool_output(capture_io):
    capture_io.tool_output("test message")
    assert capture_io.get_captured_lines() == ["test message"]
    assert capture_io.get_captured_lines() == []  # Should be empty after getting

def test_tool_output_with_log_only(capture_io):
    capture_io.tool_output("log only message", log_only=True)
    assert capture_io.get_captured_lines() == []

def test_tool_error(capture_io):
    capture_io.tool_error("error message")
    assert capture_io.get_captured_error_lines() == ["error message"]
    assert capture_io.get_captured_error_lines() == []  # Should be empty after getting

def test_tool_warning(capture_io):
    capture_io.tool_warning("warning message")
    assert capture_io.get_captured_lines() == ["warning message"]

def test_write_and_read_text(capture_io):
    capture_io.write_text("test.txt", "content")
    assert capture_io.write_files["test.txt"] == "content"
    assert capture_io.read_text("test.txt") == "content"

def test_get_captured_write_files(capture_io):
    capture_io.write_text("file1.txt", "content1")
    capture_io.write_text("file2.txt", "content2")
    
    write_files = capture_io.get_captured_write_files()
    assert write_files == {
        "file1.txt": "content1",
        "file2.txt": "content2"
    }
    assert capture_io.write_files == {}  # Should be empty after getting

def test_confirm_ask(capture_io):
    assert capture_io.confirm_ask("Create new file test.txt") == True
    assert capture_io.confirm_ask("Other question") == False
    assert capture_io.confirm_ask("Create new file", subject="test.txt") == True