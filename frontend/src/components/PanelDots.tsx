import type { PanelMember } from '../types/discussion';

interface PanelDotsProps {
  members: PanelMember[];
  maxDisplay?: number;
}

export function PanelDots({ members, maxDisplay = 5 }: PanelDotsProps) {
  const experts = members.filter((m) => m.role === 'expert');
  const display = experts.slice(0, maxDisplay);
  const remaining = experts.length - maxDisplay;

  return (
    <div className="flex items-center gap-1">
      {display.map((e) => (
        <span
          key={e.id}
          className="inline-flex items-center justify-center w-[18px] h-[18px] rounded-full text-[9px] font-bold text-white font-[var(--font-heading)] border border-white/15"
          style={{ backgroundColor: e.color }}
          title={e.name}
        >
          {e.name.charAt(0)}
        </span>
      ))}
      {remaining > 0 && (
        <span className="inline-flex items-center justify-center w-[18px] h-[18px] rounded-full bg-[var(--color-studio-hover)] text-[var(--color-studio-fg-dim)] text-[8px] font-[var(--font-heading)]">
          +{remaining}
        </span>
      )}
    </div>
  );
}
