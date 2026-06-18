import type { ReactNode } from 'react';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      {icon && <div className="mb-4 text-[var(--color-studio-fg-subtle)]">{icon}</div>}
      <h3 className="text-lg font-semibold text-[var(--color-studio-fg)] mb-1">{title}</h3>
      {description && <p className="text-sm text-[var(--color-studio-fg-muted)] mb-4 max-w-xs">{description}</p>}
      {action}
    </div>
  );
}
