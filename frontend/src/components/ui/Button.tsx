import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md';
  loading?: boolean;
  iconLeft?: React.ReactNode;
}

const variantStyles: Record<string, string> = {
  primary:
    'bg-[var(--color-studio-accent)] border-[var(--color-studio-accent)] text-black font-semibold hover:bg-[var(--color-studio-accent-dim)]',
  secondary:
    'bg-[var(--color-studio-card)] border-[var(--color-studio-border)] text-[var(--color-studio-fg)] hover:bg-[var(--color-studio-hover)]',
  danger:
    'border-[var(--color-studio-destructive)] text-[var(--color-studio-destructive)] hover:bg-[var(--color-studio-destructive)] hover:text-white',
  ghost:
    'bg-transparent border-transparent text-[var(--color-studio-fg-muted)] hover:bg-[var(--color-studio-hover)] hover:border-[var(--color-studio-border-light)]',
};

const sizeStyles: Record<string, string> = {
  sm: 'py-[5px] px-[12px] text-xs',
  md: 'py-[8px] px-[18px] text-sm',
};

export function Button({
  variant = 'secondary',
  size = 'md',
  loading = false,
  iconLeft,
  disabled,
  children,
  className = '',
  ...rest
}: ButtonProps) {
  const cls = [
    'inline-flex items-center gap-[6px] border rounded-[var(--radius-sm)] font-medium cursor-pointer transition-all duration-200 select-none whitespace-nowrap',
    variantStyles[variant],
    sizeStyles[size],
    (disabled || loading) ? 'opacity-40 cursor-not-allowed' : '',
    className,
  ].join(' ');

  return (
    <button className={cls} disabled={disabled || loading} {...rest}>
      {loading ? (
        <span className="inline-block w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
      ) : iconLeft ? (
        iconLeft
      ) : null}
      {children}
    </button>
  );
}
