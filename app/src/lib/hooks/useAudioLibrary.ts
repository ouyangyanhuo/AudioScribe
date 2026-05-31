import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';

export function useAudioLibrary(filters?: {
  language?: string;
  gender?: string;
  style?: string;
  q?: string;
}) {
  return useQuery({
    queryKey: ['audioLibrary', filters],
    queryFn: () => apiClient.listAudioLibrary(filters),
  });
}

export function useAddAudioLibraryItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: apiClient.uploadAudioLibraryItem.bind(apiClient),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['audioLibrary'] }),
  });
}

export function useUseAudioLibraryAsSample() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      itemId,
      profileId,
      referenceText,
    }: {
      itemId: string;
      profileId: string;
      referenceText: string;
    }) => apiClient.useAudioLibraryAsSample(itemId, profileId, referenceText),
    onSuccess: (_result, variables) => {
      queryClient.invalidateQueries({ queryKey: ['profileSamples', variables.profileId] });
      queryClient.invalidateQueries({ queryKey: ['profiles'] });
    },
  });
}
