import { useEffect, useRef } from 'react';
import { useToastStore } from '../../store/useToastStore';

const typeStyles: Record<string, string> = {
  info: 'border-l-[var(--color-studio-info)]',
  success: 'border-l-[var(--color-studio-success)]',
  warning: 'border-l-[var(--color-studio-warning)]',
  error: 'border-l-[var(--color-studio-destructive)]',
};

const typeIcons: Record<string, string> = {
  info: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  success: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
  warning: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z',
  error: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z',
};

export function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts);
  const removeToast = useToastStore((s) => s.removeToast);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-[var(--z-modal)] flex flex-col gap-2 max-w-sm">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onRemove={() => removeToast(t.id)} />
      ))}
    </div>
  );
}

function ToastItem({ toast, onRemove }: { toast: { id: string; type: string; message: string }; onRemove: () => void }) {
  const timer = useRef<ReturnType<typeof setTimeout>>(null);

  useEffect(() => {
    timer.current = setTimeout(onRemove, 3000);
    return () => { if (timer.current) clearTimeout(timer.current); };
  }, []);

  return (
    <div
      className={`flex items-start gap-2 px-4 py-3 bg-[var(--color-studio-elevated)]
        border border-[var(--color-studio-border)] border-l-4 ${typeStyles[toast.type]}
        rounded-lg shadow-[var(--shadow-card)] animate-fade-in cursor-pointer`}
      onClick={onRemove}
    >
      <svg className="w-5 h-5 mt-0.5 shrink-0 text-[var(--color-studio-fg)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d={typeIcons[toast.type]} />
      </svg>
      <span className="text-sm text-[var(--color-studio-fg)]">{toast.message}</span>
    </div>
  );
}
