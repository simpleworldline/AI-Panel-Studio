import { useEffect, useRef, type ReactNode } from 'react';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
}

export function Modal({ open, onClose, title, children, footer }: ModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-[var(--z-modal)] flex items-center justify-center"
      onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}
    >
      {/* backdrop */}
      <div className="absolute inset-0 bg-black/60" />
      {/* panel */}
      <div className="relative w-full max-w-md mx-4 bg-[var(--color-studio-elevated)]
        border border-[var(--color-studio-border)] rounded-xl shadow-[var(--shadow-card)]
        animate-fade-in">
        {/* header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-[var(--color-studio-border)]">
          <h3 className="text-sm font-semibold text-[var(--color-studio-fg)]">{title}</h3>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-[var(--color-studio-fg-muted)]
              hover:text-[var(--color-studio-fg)] hover:bg-[var(--color-studio-bg)]
              transition-colors duration-150 cursor-pointer"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>
        {/* body */}
        <div className="px-5 py-4">{children}</div>
        {/* footer */}
        {footer && (
          <div className="flex items-center justify-end gap-2 px-5 py-3 border-t border-[var(--color-studio-border)]">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
