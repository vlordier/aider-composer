import logging
import os
from threading import Event
from typing import Any, Dict, Iterator, List, Literal, Optional

from aider.coders import Coder
from aider.io import InputOutput
from aider.models import Model

from server.models import (
    ChatChunkData,
    ChatSessionData,
    ChatSessionReference,
    ChatSetting,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# provider_env_map maps provider names to the environment variables that need to be set
provider_env_map = {
    "deepseek": "DEEPSEEK_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "ollama": {
        "base_url": "OLLAMA_API_BASE",
    },
    "openrouter": "OPENROUTER_API_KEY",
    "openai_compatible": {
        "api_key": "OPENAI_API_KEY",
        "base_url": "OPENAI_API_BASE",
    },
}


ChatModeType = Literal["ask", "code"]


class CaptureIO(InputOutput):
    lines: List[str]
    error_lines: List[str]
    write_files: Dict[str, str]

    def __init__(
        self,
        *,
        pretty: bool | None = None,
        yes: bool | None = None,
        **kwargs: Any,
    ) -> None:
        self.lines = []
        # when spawned in node process, tool_error will be called
        # so we need to create before super().__init__
        self.error_lines = []
        self.write_files = {}
        super().__init__(pretty=pretty, yes=yes, **kwargs)

    def tool_output(
        self, msg: str = "", *, log_only: bool = False, bold: bool = False
    ) -> None:
        if not log_only:
            self.lines.append(msg)
        super().tool_output(msg, log_only=log_only, bold=bold)

    def tool_error(self, msg: str) -> None:
        self.error_lines.append(msg)
        super().tool_error(msg)

    def tool_warning(self, msg: str) -> None:
        self.lines.append(msg)
        super().tool_warning(msg)

    def get_captured_lines(self) -> List[str]:
        lines = self.lines
        self.lines = []
        return lines

    def get_captured_error_lines(self) -> List[str]:
        lines = self.error_lines
        self.error_lines = []
        return lines

    def write_text(self, filename: str, content: str) -> None:
        self.write_files[filename] = content

    def read_text(self, filename: str) -> str:
        if filename in self.write_files:
            return self.write_files[filename]
        return super().read_text(filename)

    def get_captured_write_files(self) -> Dict[str, str]:
        write_files = self.write_files
        self.write_files = {}
        return write_files

    def confirm_ask(
        self,
        question: str,
        *,  # Force keyword arguments
        subject: Optional[str] = None,
        group: Optional[str] = None,
    ) -> bool:
        logger.info("confirm_ask %s %s %s", question, subject, group)
        # create new file
        if "Create new file" in question:
            return True
        return False


class ChatSessionManager:
    chat_type: ChatModeType
    diff_format: str
    reference_list: List[ChatSessionReference]
    setting: Optional[ChatSetting] = None
    confirm_ask_result: Optional[Any] = None

    def __init__(self) -> None:
        model = Model("gpt-4o")
        io = CaptureIO(
            pretty=False,
            yes=False,
            dry_run=False,
            encoding="utf-8",
            fancy_input=False,
        )
        self.io = io

        coder = Coder.create(
            main_model=model,
            io=io,
            edit_format="ask",
            use_git=False,
        )
        coder.yield_stream = True
        coder.stream = True
        coder.pretty = False

        self.coder = coder
        self.chat_type = "ask"
        self.diff_format = "diff"
        self.reference_list = []

        self.confirm_ask_event = Event()

    def update_model(self, setting: ChatSetting) -> None:
        if self.setting != setting:
            self.setting = setting
            model = Model(setting.model)
            # update os env
            config = provider_env_map[setting.provider]

            if isinstance(config, str):
                os.environ[config] = setting.api_key

            # explicitly handle configs that need multiple env variables, like base urls and api keys
            elif isinstance(config, dict):
                for key, value in config.items():
                    os.environ[value] = getattr(setting, key)
            self.coder = Coder.create(from_coder=self.coder, main_model=model)

    def update_coder(self) -> None:
        self.coder = Coder.create(
            from_coder=self.coder,
            edit_format=self.chat_type if self.chat_type == "ask" else self.diff_format,
            fnames=(item.fs_path for item in self.reference_list if not item.readonly),
            read_only_fnames=(
                item.fs_path for item in self.reference_list if item.readonly
            ),
        )

    def _process_message(self, message: str) -> Iterator[ChatChunkData]:
        """Process a single message and yield chat chunks"""
        self.coder.reflected_message = None
        for msg in self.coder.run_stream(message):
            yield ChatChunkData(event="data", data={"chunk": msg})

        if self.coder.usage_report:
            yield ChatChunkData(event="usage", data=self.coder.usage_report)

    def _handle_error_lines(self, error_lines: List[str]) -> Iterator[ChatChunkData]:
        """Handle error lines and yield appropriate chat chunks"""
        if error_lines:
            raise RuntimeError("\n".join(error_lines))
        return iter(())  # Return empty iterator

    def _handle_reflection(self) -> Optional[str]:
        """Handle reflection and return next message if applicable"""
        if not self.coder.reflected_message:
            return None

        if self.coder.num_reflections >= self.coder.max_reflections:
            self.coder.io.tool_warning(
                f"Only {self.coder.max_reflections} reflections allowed, stopping.",
            )
            return None

        self.coder.num_reflections += 1
        return self.coder.reflected_message

    def chat(self, data: ChatSessionData) -> Iterator[ChatChunkData]:
        need_update_coder = False
        data.reference_list.sort(key=lambda x: x.fs_path)

        if data.chat_type != self.chat_type or data.diff_format != self.diff_format:
            need_update_coder = True
            self.chat_type = "ask" if data.chat_type == "ask" else "code"
            self.diff_format = data.diff_format
        if data.reference_list != self.reference_list:
            need_update_coder = True
            self.reference_list = data.reference_list

        if need_update_coder:
            self.update_coder()

        try:
            self.coder.init_before_message()
            message = data.message

            while message:
                yield from self._process_message(message)
                error_lines = self.coder.io.get_captured_error_lines()

                try:
                    yield from self._handle_error_lines(error_lines)
                except RuntimeError as e:
                    yield ChatChunkData(event="error", data={"error": str(e)})
                    return

                next_message = self._handle_reflection()
                message = next_message if next_message is not None else ""
                if message:
                    yield ChatChunkData(event="reflected", data={"message": message})

            write_files = self.io.get_captured_write_files()
            if write_files:
                yield ChatChunkData(event="write", data={"write": write_files})

        except RuntimeError as e:
            yield ChatChunkData(event="error", data={"error": str(e)})
        finally:
            yield ChatChunkData(event="end")

    def confirm_ask(self) -> None:
        self.confirm_ask_event.clear()
        self.confirm_ask_event.wait()

    def confirm_ask_reply(self) -> None:
        self.confirm_ask_event.set()


chat_session_manager = ChatSessionManager()
