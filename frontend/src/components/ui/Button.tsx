import type { ButtonHTMLAttributes, ReactNode } from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: ReactNode;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    'bg-[var(--color-studio-info)] text-white hover:brightness-110 active:brightness-90 disabled:opacity-50',
  secondary:
    'bg-[var(--color-studio-elevated)] text-[var(--color-studio-fg)] border border-[var(--color-studio-border)] hover:bg-[var(--color-studio-card)] disabled:opacity-50',
  ghost:
    'bg-transparent text-[var(--color-studio-fg-muted)] hover:text-[var(--color-studio-fg)] hover:bg-[var(--color-studio-elevated)] disabled:opacity-50',
  danger:
    'bg-[var(--color-studio-destructive)] text-white hover:brightness-110 active:brightness-90 disabled:opacity-50',
};

const sizeClasses: Record<string, string> = {
  sm: 'px-3 py-1.5 text-xs rounded-md',
  md: 'px-4 py-2 text-sm rounded-lg',
  lg: 'px-6 py-3 text-base rounded-lg',
};

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  children,
  disabled,
  className = '',
  ...props
}: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 font-medium
        transition-colors duration-150 cursor-pointer
        ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
      {children}
    </button>
  );
}
