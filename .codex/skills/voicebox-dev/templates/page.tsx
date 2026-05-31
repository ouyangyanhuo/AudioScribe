import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/utils/cn';

interface <PageName>Props {
  className?: string;
}

export function <PageName>({ className }: <PageName>Props) {
  const { t } = useTranslation();

  return (
    <div className={cn('flex flex-col h-full p-6', className)}>
      <h1 className="text-3xl font-bold mb-6">{t('<pageName>.title')}</h1>

      <div className="flex-1 min-h-0">
        {/* Page content */}
      </div>
    </div>
  );
}
