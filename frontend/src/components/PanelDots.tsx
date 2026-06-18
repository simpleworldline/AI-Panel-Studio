interface PanelDotsProps {
  count: number;
  className?: string;
}

export function PanelDots({ count, className = '' }: PanelDotsProps) {
  const colors = [
    '#6366F1', '#EF4444', '#10B981', '#F59E0B',
    '#8B5CF6', '#EC4899', '#06B6D4', '#F97316',
  ];

  return (
    <div className={`flex items-center gap-1 ${className}`}>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="w-2 h-2 rounded-full"
          style={{ backgroundColor: colors[i % colors.length] }}
        />
      ))}
    </div>
  );
}
