import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { useToast } from '@/components/ui/use-toast';
import { useMyItems, useCreateMyItem, useDeleteMyItem } from '@/lib/hooks/useMyItems';
import { cn } from '@/lib/utils/cn';

/**
 * MyFeaturePage — main page component for the /my-feature route.
 *
 * This component composes sub-components and handles page-level state.
 * Business logic lives in hooks (useMyItems, etc.), not here.
 */
export function MyFeaturePage() {
  const { data: items, isLoading, error } = useMyItems();
  const [search, setSearch] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);

  if (isLoading) {
    return <LoadingState />;
  }

  if (error) {
    return <ErrorState message={error.message} />;
  }

  const filteredItems = items?.filter((item) =>
    item.name.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">My Feature</h1>
        <div className="flex items-center gap-2">
          <Input
            placeholder="Search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-64"
          />
          <Button onClick={() => setDialogOpen(true)}>Add Item</Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {filteredItems?.length === 0 ? (
          <EmptyState onAdd={() => setDialogOpen(true)} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredItems?.map((item) => (
              <ItemCard key={item.id} item={item} />
            ))}
          </div>
        )}
      </div>

      {/* Create dialog */}
      <CreateItemDialog open={dialogOpen} onOpenChange={setDialogOpen} />
    </div>
  );
}

// --- Sub-components (same file, not exported) ---

interface ItemCardProps {
  item: { id: string; name: string; description?: string };
}

function ItemCard({ item }: ItemCardProps) {
  const deleteMutation = useDeleteMyItem();
  const { toast } = useToast();

  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync(item.id);
      toast({ title: 'Item deleted' });
    } catch (error) {
      toast({
        title: 'Delete failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="bg-card rounded-lg p-4 border border-border">
      <h3 className="font-medium">{item.name}</h3>
      {item.description && (
        <p className="text-sm text-muted-foreground mt-1">{item.description}</p>
      )}
      <div className="mt-3 flex gap-2">
        <Button variant="ghost" size="sm">
          Edit
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="text-destructive"
          onClick={handleDelete}
          disabled={deleteMutation.isPending}
        >
          Delete
        </Button>
      </div>
    </div>
  );
}

interface CreateItemDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function CreateItemDialog({ open, onOpenChange }: CreateItemDialogProps) {
  const createMutation = useCreateMyItem();
  const { toast } = useToast();
  const [name, setName] = useState('');

  const handleSubmit = async () => {
    if (!name.trim()) return;

    try {
      await createMutation.mutateAsync({ name: name.trim() });
      toast({ title: 'Item created' });
      setName('');
      onOpenChange(false);
    } catch (error) {
      toast({
        title: 'Create failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Item</DialogTitle>
        </DialogHeader>
        <div className="py-4">
          <Input
            placeholder="Item name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          />
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={createMutation.isPending || !name.trim()}>
            {createMutation.isPending ? 'Creating...' : 'Create'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function LoadingState() {
  return (
    <div className="h-full flex items-center justify-center">
      <div className="text-muted-foreground">Loading...</div>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="h-full flex items-center justify-center">
      <div className="text-destructive">Error: {message}</div>
    </div>
  );
}

function EmptyState({ onAdd }: { onAdd: () => void }) {
  return (
    <div className="h-full flex flex-col items-center justify-center gap-4">
      <p className="text-muted-foreground">No items yet</p>
      <Button onClick={onAdd}>Add your first item</Button>
    </div>
  );
}
