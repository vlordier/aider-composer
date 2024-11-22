# aider-composer

Aider Composer is a VSCode extension that integrates [Aider](https://github.com/Aider-AI/aider) into your development workflow. This extension is highly inspired by [cursor](https://www.cursor.com/) and [cline](https://github.com/cline/cline).

![demo](./resources/demo.gif)

It is highly recommended to read the [Requirements](#requirements) and [Extension Settings](#extension-settings) sections for initial configuration, otherwise the extension may not work correctly.

## Features

- Easily add and remove files, and toggle between read-only and editable modes with just a click
- Most chat modes are supported, including `ask`, `diff`, `diff-fenced`, `udiff`, and `whole`, and you can easily switch between them
- Review code changes before applying them, support both inline diff preview and diff editor preview (default).
- Chat history sessions are supported
- HTTP Proxy is supported (uses VSCode's `http.proxy` setting, authentication not supported)

### Note

Due to certain limitations and other issues, this extension may not implement all features available in Aider. Some limitations include:

- Multiple workspaces are not supported
- Git repository features are not used
- Linting is not supported
- Testing is not supported
- Voice features are not supported
- In-chat commands are not usable
- Configuration options are not supported

## Requirements

This extension uses the Python packages `aider-chat` and `flask` to provide background services. You need to:

- Install Python (download from [python.org](https://www.python.org/) or use other methods). For Mac or Python venv installations, please refer to [this issue](https://github.com/lee88688/aider-composer/issues/2)
- Install the required packages using: `pip install aider-chat flask`

## Extension Settings

This extension contributes the following setting:

- `aider-composer.pythonPath`: The directory containing the Python executable (not the Python executable path itself) where `aider.chat` and `flask` packages are installed. This setting is required for the extension to activate.

## How To Use

### Chat Mode

Aider supports five chat modes: `ask`, `diff`, `diff-fenced`, `udiff`, and `whole`. In this extension, you can switch between them by clicking the mode name in the chat input area.

The chat modes are divided into two groups: `ask` and `code`.

- `ask` mode is for general questions and will not modify any files
- `code` mode includes all other chat modes and is used for code modifications. The optimal chat mode may vary depending on your LLM model and programming language. For more information, refer to [Aider's leaderboards](https://aider.chat/docs/leaderboards/).

#### Tips

- If the LLM outputs an incorrect diff format, code modifications may fail. Try switching to a different diff format
- The leaderboard is tested with Python code, so optimal modes may differ for other languages
- The `whole` mode may be the easiest for LLMs to understand but can consume more tokens

![chat-mode](./resources/chat-mode.gif)

### File Reference

In Aider, you can reference files in the chat, file reference can be readonly or editable. a readonly file can't be modified.

In this extension, file reference is above the chat input area, you can click the file name to toggle the reference mode. when reference is **highlighted border**, it means the file is **editable**. there is two ways to add a new file reference:

- click add button and add references, this references is readonly by default.
- use `@` to reference a file in chat input area, this file will be editable by default.

![file-reference](./resources/file-reference.gif)

### Confirm Modify

when Aider modify code, it will show you a diff editor, you can review the code changes and confirm to apply them by clicking the button `✔` at editor toolbar.

![confirm-modify](./resources/confirm-modify.png)

---

**Enjoy!**
