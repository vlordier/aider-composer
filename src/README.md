# AiderChatService

The `AiderChatService` class in `src/aiderChatService.ts` manages the Aider chat service process.

## Overview

`AiderChatService` is responsible for starting, stopping, and monitoring the aider-chat service, which is a background Flask server that provides chat functionalities for the extension.

## Key Responsibilities

- **Service Management**: Handles starting and stopping the aider-chat process.
- **Configuration Validation**: Validates service configurations and ensures required Python packages are installed.
- **Process Monitoring**: Monitors the aider-chat process, handles retries, and logs output.
- **Environment Setup**: Prepares environment variables, including proxy settings and SSL configurations.

## Usage

### Starting the Service

```typescript
const aiderService = new AiderChatService(context, outputChannel);
aiderService.start();
```

### Stopping the Service

```typescript
aiderService.stop();
```

### Restarting the Service

```typescript
aiderService.restart();
```

## Important Methods

- `start()`: Starts the aider-chat service with configuration validation and retry mechanisms.
- `stop()`: Stops the aider-chat service and cleans up resources.
- `restart()`: Restarts the aider-chat service.
- `getPort()`: Retrieves the port number on which the aider-chat service is running.

## Environment Configuration

- **Python Path**: The service reads the Python path from the `aider-composer.pythonPath` setting or the VS Code Python extension.
- **Required Packages**: Ensures that `aider-chat` and `flask` packages are installed in the Python environment.
- **Proxy Settings**: Reads proxy configurations from VS Code's `http.proxy` settings.
- **SSL Verification**: Configurable via `http.proxyStrictSSL` setting.

## Error Handling

- Implements robust error handling with retries and detailed logging.
- Captures and logs errors from the aider-chat process.
- Validates configurations and environment before starting the service.

## Dependencies

- **Node.js Modules**:
  - `child_process`
  - `fs/promises`
  - `path`
  - `readline`
- **VS Code API**:
  - `vscode`
- **Python Packages**:
  - `aider-chat`
  - `flask`

## Notes

- The aider-chat service is essential for providing chat functionalities within the extension.
- Make sure to configure the `pythonPath` setting correctly and install the required Python packages as described in the main `README.md`.
