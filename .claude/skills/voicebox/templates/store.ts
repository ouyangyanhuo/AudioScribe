import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// --- Store interface ---
// Define all state fields and action methods here.
// Keep interface and implementation in the same file.

interface MyState {
  // State fields
  selectedId: string | null;
  items: Map<string, MyItem>;
  isLoading: boolean;

  // Actions
  setSelectedId: (id: string | null) => void;
  addItem: (item: MyItem) => void;
  removeItem: (id: string) => void;
  updateItem: (id: string, updates: Partial<MyItem>) => void;
  setLoading: (loading: boolean) => void;
  reset: () => void;
}

interface MyItem {
  id: string;
  name: string;
  value: number;
}

// --- Store implementation ---
// Pattern: create<Interface>()(...)
// Use set() to update state, get() to read current state.

export const useMyStore = create<MyState>((set, get) => ({
  // Initial state
  selectedId: null,
  items: new Map(),
  isLoading: false,

  // Actions
  setSelectedId: (id) => set({ selectedId: id }),

  addItem: (item) =>
    set((state) => {
      const next = new Map(state.items);
      next.set(item.id, item);
      return { items: next };
    }),

  removeItem: (id) =>
    set((state) => {
      const next = new Map(state.items);
      next.delete(id);
      return { items: next };
    }),

  updateItem: (id, updates) =>
    set((state) => {
      const existing = state.items.get(id);
      if (!existing) return state;
      const next = new Map(state.items);
      next.set(id, { ...existing, ...updates });
      return { items: next };
    }),

  setLoading: (isLoading) => set({ isLoading }),

  reset: () =>
    set({
      selectedId: null,
      items: new Map(),
      isLoading: false,
    }),
}));

// --- Persisted store variant ---
// Use persist() middleware for state that should survive page reloads.
// Use partialize to only persist specific fields.

interface MyPersistedState {
  // Persisted fields
  theme: 'light' | 'dark' | 'system';
  selectedProfileId: string | null;

  // Non-persisted fields (reset on reload)
  dialogOpen: boolean;

  // Actions
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  setSelectedProfileId: (id: string | null) => void;
  setDialogOpen: (open: boolean) => void;
}

export const useMyPersistedStore = create<MyPersistedState>()(
  persist(
    (set) => ({
      // Initial state
      theme: 'system',
      selectedProfileId: null,
      dialogOpen: false,

      // Actions
      setTheme: (theme) => set({ theme }),
      setSelectedProfileId: (id) => set({ selectedProfileId: id }),
      setDialogOpen: (open) => set({ dialogOpen: open }),
    }),
    {
      name: 'voicebox-my-feature', // localStorage key
      partialize: (state) => ({
        // Only persist these fields
        theme: state.theme,
        selectedProfileId: state.selectedProfileId,
        // dialogOpen is NOT persisted — resets to false on reload
      }),
      onRehydrateStorage: () => (state) => {
        // Optional: run side effects after rehydration
        if (state) {
          // e.g., apply theme to DOM
        }
      },
    },
  ),
);
