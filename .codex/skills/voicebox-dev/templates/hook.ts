import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import type { <Domain>Response, <Domain>Create } from '@/lib/api/types';

// Query key
const KEY = ['<domain>'];

/**
 * Fetch the list of <domain> items.
 */
export function use<Domain>List() {
  return useQuery({
    queryKey: KEY,
    queryFn: () => apiClient.list<Domain>(),
  });
}

/**
 * Fetch a single <domain> item by ID.
 */
export function use<Domain>(id: string) {
  return useQuery({
    queryKey: [...KEY, id],
    queryFn: () => apiClient.get<Domain>(id),
    enabled: !!id,
  });
}

/**
 * Create a new <domain> item.
 */
export function useCreate<Domain>() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: <Domain>Create) => apiClient.create<Domain>(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: KEY });
    },
  });
}

/**
 * Update an existing <domain> item.
 */
export function useUpdate<Domain>() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<<Domain>Create> }) =>
      apiClient.update<Domain>(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: KEY });
      queryClient.invalidateQueries({ queryKey: [...KEY, variables.id] });
    },
  });
}

/**
 * Delete a <domain> item.
 */
export function useDelete<Domain>() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiClient.delete<Domain>(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: KEY });
    },
  });
}
