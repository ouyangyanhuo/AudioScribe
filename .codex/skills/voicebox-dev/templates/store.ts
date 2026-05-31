import { create } from 'zustand';
// Uncomment for persistence:
// import { persist } from 'zustand/middleware';

interface <Domain>State {
  // State fields
  selectedId: string | null;
  isDialogOpen: boolean;

  // Actions
  setSelectedId: (id: string | null) => void;
  setDialogOpen: (open: boolean) => void;
  reset: () => void;
}

export const use<Domain>Store = create<<Domain>State>((set) => ({
  selectedId: null,
  isDialogOpen: false,

  setSelectedId: (id) => set({ selectedId: id }),
  setDialogOpen: (open) => set({ isDialogOpen: open }),
  reset: () => set({ selectedId: null, isDialogOpen: false }),
}));

// Uncomment for persistence:
// export const use<Domain>Store = create<<Domain>State>()(
//   persist(
//     (set) => ({
//       selectedId: null,
//       isDialogOpen: false,
//
//       setSelectedId: (id) => set({ selectedId: id }),
//       setDialogOpen: (open) => set({ isDialogOpen: open }),
//       reset: () => set({ selectedId: null, isDialogOpen: false }),
//     }),
//     {
//       name: 'voicebox-<domain>',
//       partialize: (state) => ({ selectedId: state.selectedId }),
//     },
//   ),
// );
