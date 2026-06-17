import { useToastStore } from '../../store/useToastStore';

const typeStyles: Record<string, string> = {
  success: 'border-l-[var(--color-studio-accent)]',
  error: 'border-l-[var(--color-studio-destructive)]',
  warning: 'border-l-[var(--color-studio-warning)]',
  info: 'border-l-[var(--color-studio-info)]',
};

export function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts);
  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-5 right-5 z-[var(--z-modal)] flex flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`bg-[var(--color-studio-card)] border border-[var(--color-studio-border)] border-l-4 rounded-[var(--radius-sm)] px-4 py-3 text-sm max-w-[360px] shadow-lg ${typeStyles[t.type]}`}
          style={{ animation: 'slide-up 0.2s ease-out' }}
        >
          {t.message}
        </div>
      ))}
    </div>
  );
}
