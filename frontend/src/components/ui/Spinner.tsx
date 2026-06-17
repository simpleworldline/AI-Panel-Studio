interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
}

const sizeMap = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-8 h-8' };

export function Spinner({ size = 'md' }: SpinnerProps) {
  return (
    <div
      className={`${sizeMap[size]} border-2 border-[var(--color-studio-border)] border-t-[var(--color-studio-accent)] rounded-full animate-spin`}
    />
  );
}
