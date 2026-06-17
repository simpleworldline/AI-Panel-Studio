import React, { useEffect, useCallback } from 'react';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg';
}

const sizeMap = { sm: 'max-w-[420px]', md: 'max-w-[480px]', lg: 'max-w-[640px]' };

export function Modal({ open, onClose, title, children, footer, size = 'md' }: ModalProps) {
  const handleKey = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    },
    [onClose],
  );

  useEffect(() => {
    if (open) {
      document.addEventListener('keydown', handleKey);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleKey);
      document.body.style.overflow = '';
    };
  }, [open, handleKey]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-[4px] flex items-center justify-center z-[var(--z-modal)]"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        className={`bg-[var(--color-studio-elevated)] border border-[var(--color-studio-border)] rounded-[var(--radius-lg)] p-7 w-[90%] ${sizeMap[size]}`}
        style={{ animation: 'slide-up 0.25s ease-out' }}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <h2 className="font-[var(--font-heading)] text-lg font-bold mb-5">{title}</h2>
        <div>{children}</div>
        {footer && <div className="flex justify-end gap-3 mt-6">{footer}</div>}
      </div>
    </div>
  );
}
