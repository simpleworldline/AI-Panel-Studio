import type { PanelMember } from '../types/discussion';
import type { ExpertStatus } from '../types/expert';
import { ExpertCard } from './ExpertCard';

interface ExpertStatusPanelProps {
  members: PanelMember[];
  statuses: Record<string, ExpertStatus>;
  compact?: boolean;
}

export function ExpertStatusPanel({ members, statuses, compact = false }: ExpertStatusPanelProps) {
  const sorted = [...members].sort((a, b) => a.sortOrder - b.sortOrder);

  return (
    <div className="flex flex-col gap-2.5">
      {sorted.map((m) => (
        <ExpertCard
          key={m.id}
          member={m}
          status={statuses[m.id]}
          compact={compact}
        />
      ))}
    </div>
  );
}
