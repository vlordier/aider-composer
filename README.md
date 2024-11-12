# aider-composer

Aider Composer is a VSCode extension that allows you to integrate [Aider](https://github.com/Aider-AI/aider) into your development workflow. this extension is highly inspired by [cursor](https://www.cursor.com/) and [cline](https://github.com/cline/cline).

## Features

- easily add and drop file.
- most of the chat mode is supported, including `ask` `diff` `diff-fenced` `udiff` `whole`, and you can easily switch between them.
- review code changes before applying them.
- HTTP Proxy is supported, use VSCode settings `http.proxy` to configure and don't support authentication.

### Note

because of some limitation or other issues, this extension may not implement all features in Aider, some are listed here:

- multiple workspaces are not supported
- git, extension will not use git repo features
- lint
- test
- voice
- in-chat commands are not usable
- configuration is not supported

## Requirements

This extension use python package `aider.chat` and `flask` to provide background service, so you should install them first.

- install Python
- install `aider.chat` and `flask` package

## Extension Settings

This extension contributes the following settings:

- `aider-composer.pythonPath`: Path that includes the Python executable and the `aider.chat`, `flask` package is installed. this is required before you can use this extension. if you not set this, extension will not be activated.

---

## Following extension guidelines

Ensure that you've read through the extensions guidelines and follow the best practices for creating your extension.

- [Extension Guidelines](https://code.visualstudio.com/api/references/extension-guidelines)

## Working with Markdown

You can author your README using Visual Studio Code. Here are some useful editor keyboard shortcuts:

- Split the editor (`Cmd+\` on macOS or `Ctrl+\` on Windows and Linux).
- Toggle preview (`Shift+Cmd+V` on macOS or `Shift+Ctrl+V` on Windows and Linux).
- Press `Ctrl+Space` (Windows, Linux, macOS) to see a list of Markdown snippets.

## For more information

- [Visual Studio Code's Markdown Support](http://code.visualstudio.com/docs/languages/markdown)
- [Markdown Syntax Reference](https://help.github.com/articles/markdown-basics/)

**Enjoy!**
