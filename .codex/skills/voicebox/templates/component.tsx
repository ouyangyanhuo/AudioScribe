import { cn } from '@/lib/utils/cn';

interface MyComponentProps {
  /** Primary content */
  title: string;
  /** Visual variant */
  variant?: 'default' | 'compact' | 'expanded';
  /** Additional CSS classes */
  className?: string;
  /** Child elements */
  children: React.ReactNode;
}

/**
 * MyComponent — brief description of what this component does.
 *
 * Usage:
 * ```tsx
 * <MyComponent title="Hello" variant="default">
 *   <p>Content here</p>
 * </MyComponent>
 * ```
 */
export function MyComponent({
  title,
  variant = 'default',
  className,
  children,
}: MyComponentProps) {
  return (
    <div
      className={cn(
        'base-classes',
        variant === 'compact' && 'compact-specific-classes',
        variant === 'expanded' && 'expanded-specific-classes',
        className,
      )}
    >
      <h2 className="text-xl font-semibold">{title}</h2>
      <div className="mt-2">{children}</div>
    </div>
  );
}

// --- Sub-component (same file, not exported) ---

interface SubComponentProps {
  label: string;
  isActive?: boolean;
  onClick: () => void;
}

function SubComponent({ label, isActive = false, onClick }: SubComponentProps) {
  return (
    <button
      type="button"
      className={cn(
        'px-3 py-1.5 text-sm rounded-md transition-colors',
        isActive
          ? 'bg-accent text-accent-foreground'
          : 'text-muted-foreground hover:bg-secondary hover:text-secondary-foreground',
      )}
      onClick={onClick}
    >
      {label}
    </button>
  );
}
