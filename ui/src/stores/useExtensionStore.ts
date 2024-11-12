import { create } from 'zustand';
import { combine } from 'zustand/middleware';

const useExtensionStore = create(
  combine(
    {
      isStarted: false,
      viewType: 'welcome',
      serverUrl:
        import.meta.env.NODE_ENV === 'development'
          ? 'http://localhost:5000'
          : '',
      errorMessage: '',
    },
    (set) => ({
      setViewType: (viewType: string) => set({ viewType }),
    }),
  ),
);

export default useExtensionStore;
