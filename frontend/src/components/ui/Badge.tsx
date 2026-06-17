import React from 'react';

interface BadgeProps {
  variant: 'live' | 'ended' | 'consensus' | 'disagreement' | 'idle' | 'preparing' | 'speaking';
  dot?: boolean;
  children: React.ReactNode;
}

const variantStyles: Record<string, string> = {
  live: 'bg-[rgba(34,197,94,0.12)] text-[var(--color-studio-accent)]',
  ended: 'bg-[rgba(100,116,139,0.12)] text-[var(--color-studio-fg-dim)]',
  consensus: 'bg-[rgba(52,211,153,0.10)] text-[var(--color-consensus-green)]',
  disagreement: 'bg-[rgba(251,146,60,0.10)] text-[var(--color-consensus-orange)]',
  idle: 'bg-[rgba(100,116,139,0.15)] text-[var(--color-status-idle)]',
  preparing: 'bg-[rgba(245,158,11,0.15)] text-[var(--color-status-preparing)]',
  speaking: 'bg-[rgba(59,130,246,0.15)] text-[var(--color-status-speaking)]',
};

const labels: Record<string, string> = {
  idle: '待机',
  preparing: '准备发言',
  speaking: '发言中',
};

export function Badge({ variant, dot = true, children }: BadgeProps) {
  const label = labels[variant] || children;
  const animClass =
    variant === 'preparing'
      ? 'animate-[pulse-badge_0.8s_ease-in-out_infinite]'
      : variant === 'speaking'
        ? 'animate-[pulse-badge_0.5s_ease-in-out_infinite]'
        : '';

  return (
    <span
      className={`inline-flex items-center gap-[5px] px-[8px] py-[3px] rounded-[20px] text-[11px] font-semibold uppercase tracking-wider ${variantStyles[variant]} ${animClass}`}
    >
      {dot && (
        <span
          className={`inline-block w-[6px] h-[6px] rounded-full bg-current ${variant === 'live' ? 'animate-[pulse-dot_2s_ease-in-out_infinite]' : ''}`}
        />
      )}
      {label}
    </span>
  );
}
