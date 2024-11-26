import { spawn, ChildProcess } from 'node:child_process';
import * as fsPromise from 'node:fs/promises';
import * as path from 'node:path';
import * as readline from 'node:readline';
import * as vscode from 'vscode';
import { isProductionMode } from './utils/isProductionMode';

// Constants
const SERVICE_CONSTANTS = {
  START_TIMEOUT_MS: 60000,
  MIN_PORT: 10000,
  MAX_PORT: 20000,
  DEV_PORT: 5000,
  MAX_RETRIES: 3,
  RETRY_DELAY_MS: 2000,
} as const;

class AiderServiceError extends Error {
  constructor(message: string, public readonly cause?: Error) {
    super(message);
    this.name = 'AiderServiceError';
  }
}

interface AiderConfig {
  pythonPath: string;
}

/**
 * Service class that manages the Aider chat process
 * Handles starting, stopping, and monitoring the chat service
 */
export default class AiderChatService {
  private aiderChatProcess: ChildProcess | undefined;
  private port: number = 0;
  private retryCount: number = 0;

  onStarted: () => void = () => { };
  onError: (error: Error) => void = () => { };

  constructor(
    private context: vscode.ExtensionContext,
    private outputChannel: vscode.LogOutputChannel,
  ) { }

  /**
   * Starts the Aider chat service
   * @returns Promise that resolves when service is started
   * @throws AiderServiceError if service fails to start
   */
  async start(): Promise<void> {
    this.log('info', 'Starting aider-chat service...');

    if (!isProductionMode(this.context)) {
      this.port = SERVICE_CONSTANTS.DEV_PORT;
      this.onStarted();
      return;
    }

    try {
      await this.validateConfiguration();
      await this.startServiceWithRetry();
    } catch (error) {
      const serviceError = new AiderServiceError(
        'Failed to start aider-chat service',
        error instanceof Error ? error : undefined
      );
      this.log('error', serviceError.message, error);
      this.onError(serviceError);
      throw serviceError;
    }
  }

  /**
   * Gets the current Python path from VS Code Python extension
   */
  private getCurrentPythonPath(): string | undefined {
    const pythonConfig = vscode.workspace.getConfiguration('python');
    const defaultInterpreterPath = pythonConfig.get<string>('defaultInterpreterPath');
    if (defaultInterpreterPath && defaultInterpreterPath !== 'python') {
      return defaultInterpreterPath;
    }

    const pythonPath = pythonConfig.get<string>('pythonPath');
    if (pythonPath && pythonPath !== 'python') {
      return pythonPath;
    }

    return undefined;
  }

  /**
   * Validates the service configuration
   * @throws AiderServiceError if configuration is invalid
   */
  private async validateConfiguration(): Promise<void> {
    const config = vscode.workspace.getConfiguration('aider-composer') as AiderConfig;

    // Try to get Python path from VS Code Python extension first
    const currentPythonPath = this.getCurrentPythonPath();
    let pythonPath: string;

    if (currentPythonPath) {
      pythonPath = currentPythonPath;
      // Update the settings with current Python path
      await config.update('pythonPath', path.dirname(currentPythonPath), vscode.ConfigurationTarget.Global);
      this.log('info', `Updated Python path to: ${currentPythonPath}`);
    } else {
      pythonPath = this.resolvePythonPath(config.pythonPath);
    }

    if (!pythonPath) {
      throw new AiderServiceError('Python path is not configured');
    }

    try {
      await fsPromise.access(pythonPath, fsPromise.constants.X_OK);
    } catch (error) {
      throw new AiderServiceError('Python executable not found or not executable');
    }

    // Check if the python command works
    try {
      await this.verifyPythonCommand(pythonPath);
    } catch (error) {
      throw new AiderServiceError('Python command failed', error instanceof Error ? error : undefined);
    }

    // Check if required Python packages are installed
    try {
      await this.verifyPythonPackages(pythonPath);
    } catch (error) {
      throw new AiderServiceError('Required Python packages not installed', error instanceof Error ? error : undefined);
    }

    const serverMainPath = path.join(this.context.extensionUri.fsPath, 'server', 'main.py');
    try {
      await fsPromise.access(serverMainPath, fsPromise.constants.R_OK);
    } catch (error) {
      throw new AiderServiceError(`Server main.py not found at path: ${serverMainPath}`);
    }

    if (!vscode.workspace.workspaceFolders?.length) {
      throw new AiderServiceError('No workspace folder found');
    }

    if (vscode.workspace.workspaceFolders.length > 1) {
      throw new AiderServiceError('Multiple workspace folders not supported');
    }
  }

  /**
   * Checks if the Python command works
   */
  private async verifyPythonCommand(pythonPath: string): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      const process = spawn(pythonPath, ['--version']);
      let output = '';
      process.stdout?.on('data', (data) => {
        output += data.toString();
      });
      process.stderr?.on('data', (data) => {
        output += data.toString();
      });
      process.on('close', (code) => {
        if (code === 0) {
          this.log('info', `Python version: ${output.trim()}`);
          resolve();
        } else {
          this.log('error', `Python command failed with code ${code}, output: ${output.trim()}`);
          reject(new Error(`Python command failed with code ${code}`));
        }
      });
      process.on('error', (error) => {
        this.log('error', `Python command error: ${error}`);
        reject(error);
      });
    });
  }

  /**
   * Checks if required Python packages are installed
   */
  private async verifyPythonPackages(pythonPath: string): Promise<void> {
    const requiredModules = ['flask']; // Add any other required modules here
    for (const moduleName of requiredModules) {
      try {
        await this.verifyPythonModule(pythonPath, moduleName);
      } catch (error) {
        throw new AiderServiceError(`Required Python module "${moduleName}" not installed`, error instanceof Error ? error : undefined);
      }
    }
  }

  /**
   * Verifies if a specific Python module is installed
   */
  private async verifyPythonModule(pythonPath: string, moduleName: string): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      const process = spawn(pythonPath, ['-c', `import ${moduleName}`]);
      process.on('close', (code) => {
        if (code === 0) {
          this.log('info', `Python module "${moduleName}" is installed`);
          resolve();
        } else {
          this.log('error', `Python module "${moduleName}" is not installed`);
          reject(new Error(`Python module "${moduleName}" is not installed`));
        }
      });
      process.on('error', (error) => {
        this.log('error', `Error checking for Python module "${moduleName}": ${error}`);
        reject(error);
      });
    });
  }

  /**
   * Starts the service with retry mechanism
   */
  private async startServiceWithRetry(): Promise<void> {
    while (this.retryCount < SERVICE_CONSTANTS.MAX_RETRIES) {
      try {
        this.log('info', `Attempting to start service (attempt ${this.retryCount + 1})`);
        await this.startServiceProcess();
        this.retryCount = 0; // Reset counter on success
        this.log('info', 'Service started successfully');
        return;
      } catch (error) {
        this.retryCount++;
        this.log('warn', `Service start failed, attempt ${this.retryCount}/${SERVICE_CONSTANTS.MAX_RETRIES}`, error);

        if (this.retryCount < SERVICE_CONSTANTS.MAX_RETRIES) {
          await new Promise(resolve => setTimeout(resolve, SERVICE_CONSTANTS.RETRY_DELAY_MS));
          continue;
        }
        this.log('error', 'Exceeded maximum retry attempts, service failed to start');
        throw error;
      }
    }
  }

  /**
   * Starts the actual service process
   */
  private async startServiceProcess(): Promise<void> {
    return vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: 'Starting aider-chat service...',
        cancellable: false,
      },
      async () => {
        const randomPort = Math.floor(Math.random() *
          (SERVICE_CONSTANTS.MAX_PORT - SERVICE_CONSTANTS.MIN_PORT)) + SERVICE_CONSTANTS.MIN_PORT;

        const env = this.prepareEnvironment();
        const folderPath = vscode.workspace.workspaceFolders![0].uri.fsPath;

        // Check if workspace folder exists
        try {
          await fsPromise.access(folderPath, fsPromise.constants.R_OK);
        } catch (error) {
          throw new AiderServiceError(`Workspace folder path is not accessible: ${folderPath}`, error instanceof Error ? error : undefined);
        }

        return new Promise<void>((resolve, reject) => {
          const process = this.spawnProcess(randomPort, folderPath, env);

          process.on('error', (err) => {
            this.log('error', `Failed to start process: ${err}`);
            reject(err);
          });

          this.setupProcessHandlers(process, randomPort, resolve, reject);
        });
      }
    );
  }

  /**
   * Prepares the environment variables for the process
   */
  private prepareEnvironment(): NodeJS.ProcessEnv {
    const env = { ...process.env };
    this.log('info', 'Preparing environment variables...');
    this.log('info', `Initial environment variables: ${JSON.stringify(env)}`);

    const httpConfig = vscode.workspace.getConfiguration('http');

    const proxy = httpConfig.get<string>('proxy');
    if (proxy) {
      env.HTTP_PROXY = proxy;
      env.HTTPS_PROXY = proxy;
      env.HTTPX_PROXY = proxy;
      this.log('info', `Set proxy to ${proxy}`);
    }

    if (httpConfig.get<boolean>('proxyStrictSSL') === false) {
      env.SSL_VERIFY = 'false';
      this.log('info', 'Set SSL_VERIFY to false');
    }

    return env;
  }

  /**
   * Spawns the aider-chat process
   */
  private spawnProcess(randomPort: number, folderPath: string, env: NodeJS.ProcessEnv): ChildProcess {
    const pythonPathFile = this.resolvePythonPath(vscode.workspace.getConfiguration('aider-composer').pythonPath);
    const args = [
      '-m',
      'flask',
      '-A',
      path.join(this.context.extensionUri.fsPath, 'server/main.py'),
      'run',
      '--port',
      randomPort.toString(),
    ];
    this.log('info', `Spawning aider-chat process: ${pythonPathFile} ${args.join(' ')}`);

    const aiderChatProcess = spawn(
      pythonPathFile,
      args,
      {
        cwd: folderPath,
        env,
      },
    );

    this.log('debug', 'aider-chat process spawned with PID:', aiderChatProcess.pid);
    this.aiderChatProcess = aiderChatProcess;
    return aiderChatProcess;
  }

  /**
   * Sets up handlers for the aider-chat process
   */
  private setupProcessHandlers(
    aiderChatProcess: ChildProcess,
    randomPort: number,
    resolve: () => void,
    reject: (reason?: any) => void
  ): void {
    const timer = setTimeout(() => {
      this.stop();
      const timeoutMessage = 'aider-chat service start timeout';
      this.log('error', timeoutMessage);
      reject(new AiderServiceError(timeoutMessage));
    }, SERVICE_CONSTANTS.START_TIMEOUT_MS);

    aiderChatProcess.on('error', (err) => {
      this.log('error', `aider-chat process error: ${err}`);
      reject(err);
    });

    aiderChatProcess.on('close', (code) => {
      this.log('error', `aider-chat service closed with code ${code}`);
      if (code !== 0) {
        reject(new AiderServiceError(`aider-chat service closed with code ${code}`));
      }
    });

    aiderChatProcess.on('exit', (code, signal) => {
      clearTimeout(timer);
      this.log('error', `aider-chat service exited with code ${code} and signal ${signal}`);
      if (code !== 0) {
        reject(new AiderServiceError(`aider-chat service exited with code ${code} and signal ${signal}`));
      }
    });

    let isRunning = false;
    const handleLine = (line: string) => {
      this.log('info', `aider-chat: ${line}`);
      if (
        !isRunning &&
        line.includes(`Running on http://127.0.0.1:${randomPort}`)
      ) {
        isRunning = true;
        this.port = randomPort;
        this.onStarted();
        clearTimeout(timer);
        resolve();
      } else if (line.toLowerCase().includes('error')) {
        this.log('error', `Error from aider-chat: ${line}`);
      }
    };

    if (aiderChatProcess.stderr) {
      const rl = readline.createInterface({
        input: aiderChatProcess.stderr,
      });

      rl.on('line', handleLine);
    }

    if (aiderChatProcess.stdout) {
      const rl = readline.createInterface({
        input: aiderChatProcess.stdout,
      });

      rl.on('line', handleLine);
    }
  }

  restart() {
    this.log('info', 'Restarting aider-chat service...');
    this.stop();
    this.start();
  }

  stop() {
    this.log('info', 'Stopping aider-chat service...');
    this.aiderChatProcess?.kill();
    this.aiderChatProcess = undefined;
  }

  /**
   * Logs a message with consistent formatting
   */
  private log(level: 'info' | 'warn' | 'error' | 'debug', message: string, error?: unknown): void {
    const timestamp = new Date().toISOString();
    const formattedMessage = `[${timestamp}] [${level.toUpperCase()}] ${message}`;

    this.outputChannel[level](formattedMessage);
    if (error) {
      const errorMessage = error instanceof Error ? error.stack || error.message : String(error);
      this.outputChannel[level](`[${timestamp}] [${level.toUpperCase()}] ${errorMessage}`);
    }
  }

  /**
   * Resolves the Python executable path
   */
  private resolvePythonPath(configPath: string): string {
    const pythonExecutable = process.platform === 'win32' ? 'python.exe' : 'python';
    const pythonPath = path.join(
      configPath,
      pythonExecutable
    );
    this.log('info', `Resolved Python path: ${pythonPath}`);
    return pythonPath;
  }
}
