import { Pause, Play, Search } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { apiClient } from '@/lib/api/client';
import type { AudioLibraryItem } from '@/lib/api/types';
import { useAudioLibrary } from '@/lib/hooks/useAudioLibrary';
import { formatAudioDuration } from '@/lib/utils/audio';

interface AudioLibraryBrowserProps {
  onSelect: (item: AudioLibraryItem) => void;
}

export function AudioLibraryBrowser({ onSelect }: AudioLibraryBrowserProps) {
  const [query, setQuery] = useState('');
  const [playingId, setPlayingId] = useState<string | null>(null);
  const { data: items = [], isLoading } = useAudioLibrary({ q: query || undefined });

  const audio = useMemo(() => new Audio(), []);

  function togglePreview(item: AudioLibraryItem) {
    if (playingId === item.id) {
      audio.pause();
      setPlayingId(null);
      return;
    }
    audio.pause();
    audio.src = apiClient.getAudioLibraryUrl(item.id);
    audio.onended = () => setPlayingId(null);
    audio.play().catch(() => setPlayingId(null));
    setPlayingId(item.id);
  }

  return (
    <div className="space-y-4">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          className="pl-9"
          placeholder="Search audio library"
        />
      </div>

      <div className="max-h-[360px] overflow-y-auto space-y-2">
        {isLoading ? (
          <div className="text-sm text-muted-foreground">Loading...</div>
        ) : items.length === 0 ? (
          <div className="rounded-md border border-dashed p-6 text-center text-sm text-muted-foreground">
            No audio library items yet.
          </div>
        ) : (
          items.map((item) => (
            <div key={item.id} className="flex items-center gap-3 rounded-md border p-3">
              <Button type="button" size="icon" variant="outline" onClick={() => togglePreview(item)}>
                {playingId === item.id ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </Button>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium">{item.name}</div>
                <div className="text-xs text-muted-foreground">
                  {[item.language, item.gender, item.style].filter(Boolean).join(' / ') || item.source}
                  {item.duration ? ` / ${formatAudioDuration(item.duration)}` : ''}
                </div>
              </div>
              <Button type="button" size="sm" onClick={() => onSelect(item)}>
                Select
              </Button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
