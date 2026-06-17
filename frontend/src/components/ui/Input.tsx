import React from 'react';

interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  error?: string;
  onChange: (value: string) => void;
}

export function Input({ error, onChange, className = '', ...rest }: InputProps) {
  return (
    <div className="w-full">
      <input
        className={[
          'w-full px-[14px] py-[10px] bg-[var(--color-studio-card)] border rounded-[var(--radius-sm)] text-[var(--color-studio-fg)] text-sm transition-colors duration-200 outline-none',
          error
            ? 'border-[var(--color-studio-destructive)]'
            : 'border-[var(--color-studio-border)] focus:border-[var(--color-studio-accent)] focus:ring-2 focus:ring-[var(--color-studio-accent)]/15',
          rest.disabled ? 'opacity-40 cursor-not-allowed' : '',
          className,
        ].join(' ')}
        onChange={(e) => onChange(e.target.value)}
        {...rest}
      />
      {error && <p className="mt-1 text-xs text-[var(--color-studio-destructive)]">{error}</p>}
    </div>
  );
}
