import { cn } from '@/lib/utils/cn';

interface <ComponentName>Props {
  title: string;
  variant?: 'default' | 'compact';
  className?: string;
  children?: React.ReactNode;
}

export function <ComponentName>({ title, variant = 'default', className, children }: <ComponentName>Props) {
  return (
    <div
      className={cn(
        'base-classes',
        variant === 'compact' && 'compact-classes',
        className,
      )}
    >
      <h2 className="text-lg font-medium">{title}</h2>
      {children}
    </div>
  );
}
