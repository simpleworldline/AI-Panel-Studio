import type { ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  color?: string;       // hex or CSS color
  variant?: 'solid' | 'outline' | 'dot';
  className?: string;
}

export function Badge({ children, color, variant = 'solid', className = '' }: BadgeProps) {
  const base = 'inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium rounded-full';

  if (variant === 'dot') {
    return (
      <span className={`${base} text-[var(--color-studio-fg-muted)] ${className}`}>
        <span
          className="w-2 h-2 rounded-full inline-block"
          style={{ backgroundColor: color }}
        />
        {children}
      </span>
    );
  }

  if (variant === 'outline') {
    return (
      <span
        className={`${base} border ${className}`}
        style={{ borderColor: color, color }}
      >
        {children}
      </span>
    );
  }

  // solid
  return (
    <span
      className={`${base} text-white ${className}`}
      style={{ backgroundColor: color }}
    >
      {children}
    </span>
  );
}
