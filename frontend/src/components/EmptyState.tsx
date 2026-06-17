import { Button } from './ui/Button';

interface EmptyStateProps {
  icon?: string;
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
}

export function EmptyState({ icon = '📋', title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-5 text-center gap-2">
      <span className="text-4xl opacity-20">{icon}</span>
      <p className="font-[var(--font-heading)] text-sm text-[var(--color-studio-fg-muted)]">{title}</p>
      {description && (
        <p className="text-xs text-[var(--color-studio-fg-dim)] max-w-[360px] leading-relaxed">
          {description}
        </p>
      )}
      {action && (
        <Button variant="primary" size="sm" className="mt-2" onClick={action.onClick}>
          {action.label}
        </Button>
      )}
    </div>
  );
}
