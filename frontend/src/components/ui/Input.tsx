import type { InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export function Input({ label, error, helperText, className = '', id, ...props }: InputProps) {
  const inputId = id || label?.replace(/\s+/g, '-').toLowerCase();
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={inputId} className="text-xs font-medium text-[var(--color-studio-fg-muted)]">
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={`px-3 py-2 text-sm rounded-lg bg-[var(--color-studio-bg)]
          border transition-colors duration-150 outline-none
          ${error
            ? 'border-[var(--color-studio-destructive)] focus:ring-2 focus:ring-[var(--color-studio-destructive)]/30'
            : 'border-[var(--color-studio-border)] focus:border-[var(--color-studio-info)] focus:ring-2 focus:ring-[var(--color-studio-info)]/20'
          }
          text-[var(--color-studio-fg)] placeholder:text-[var(--color-studio-fg-subtle)]
          disabled:opacity-50 disabled:cursor-not-allowed
          ${className}`}
        {...props}
      />
      {error && <span className="text-xs text-[var(--color-studio-destructive)]">{error}</span>}
      {helperText && !error && (
        <span className="text-xs text-[var(--color-studio-fg-subtle)]">{helperText}</span>
      )}
    </div>
  );
}
