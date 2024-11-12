import { createJSONStorage, StateStorage } from 'zustand/middleware';
import {
  deleteWorkspaceState,
  getWorkspaceState,
  setWorkspaceState,
} from '../commandApi';

const vscodeStorage: StateStorage = {
  getItem: (key: string) => {
    return getWorkspaceState({ key });
  },
  setItem: (key: string, value: string) => {
    return setWorkspaceState({ key, value });
  },
  removeItem: (key: string) => {
    return deleteWorkspaceState({ key });
  },
};

export const persistStorage = createJSONStorage(() => vscodeStorage);
