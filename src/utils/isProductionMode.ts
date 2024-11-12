import { ExtensionMode, ExtensionContext } from 'vscode';

export function isProductionMode(context: ExtensionContext): boolean {
  return context.extensionMode === ExtensionMode.Production;
}
