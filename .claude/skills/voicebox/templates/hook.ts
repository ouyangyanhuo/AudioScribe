import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import type { MyItemCreate, MyItemResponse } from '@/lib/api/types';

// --- Query hooks ---
// Use useQuery for data fetching. Query keys should be descriptive arrays.

const MY_ITEMS_KEY = ['my-items'];

/**
 * Fetch all items.
 */
export function useMyItems() {
  return useQuery({
    queryKey: MY_ITEMS_KEY,
    queryFn: () => apiClient.listMyItems(),
  });
}

/**
 * Fetch a single item by ID.
 * Uses `enabled` to prevent fetching when ID is falsy.
 */
export function useMyItem(itemId: string) {
  return useQuery({
    queryKey: [...MY_ITEMS_KEY, itemId],
    queryFn: () => apiClient.getMyItem(itemId),
    enabled: !!itemId,
  });
}

/**
 * Fetch nested resource (e.g., item's children).
 */
export function useMyItemChildren(itemId: string) {
  return useQuery({
    queryKey: [...MY_ITEMS_KEY, itemId, 'children'],
    queryFn: () => apiClient.listMyItemChildren(itemId),
    enabled: !!itemId,
  });
}

// --- Mutation hooks ---
// Use useMutation for data modifications.
// Always invalidate related queries in onSuccess.

/**
 * Create a new item.
 */
export function useCreateMyItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: MyItemCreate) => apiClient.createMyItem(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MY_ITEMS_KEY });
    },
  });
}

/**
 * Update an existing item.
 * Invalidates both list and detail queries.
 */
export function useUpdateMyItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ itemId, data }: { itemId: string; data: Partial<MyItemCreate> }) =>
      apiClient.updateMyItem(itemId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: MY_ITEMS_KEY });
      queryClient.invalidateQueries({
        queryKey: [...MY_ITEMS_KEY, variables.itemId],
      });
    },
  });
}

/**
 * Delete an item.
 */
export function useDeleteMyItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (itemId: string) => apiClient.deleteMyItem(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MY_ITEMS_KEY });
    },
  });
}

// --- Optimistic update example ---
// Use onMutate to update cache before the server responds.
// Use onError to rollback on failure.

/**
 * Update item settings with optimistic update.
 */
export function useMyItemSettings() {
  const queryClient = useQueryClient();
  const KEY = ['my-item-settings'];

  return useMutation({
    mutationFn: (patch: Record<string, unknown>) =>
      apiClient.updateMyItemSettings(patch),

    // Optimistic update: immediately update cache
    onMutate: async (patch) => {
      await queryClient.cancelQueries({ queryKey: KEY });
      const previous = queryClient.getQueryData(KEY);
      queryClient.setQueryData(KEY, (old: unknown) => ({ ...(old as object), ...patch }));
      return { previous };
    },

    // Rollback on error
    onError: (_err, _patch, ctx) => {
      if (ctx?.previous) {
        queryClient.setQueryData(KEY, ctx.previous);
      }
    },

    // Settle with server response
    onSettled: (data) => {
      if (data) queryClient.setQueryData(KEY, data);
    },
  });
}

// --- File upload example ---

/**
 * Upload a file associated with an item.
 */
export function useUploadMyItemFile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ itemId, file }: { itemId: string; file: File }) =>
      apiClient.uploadMyItemFile(itemId, file),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: MY_ITEMS_KEY });
      queryClient.invalidateQueries({
        queryKey: [...MY_ITEMS_KEY, variables.itemId],
      });
    },
  });
}
