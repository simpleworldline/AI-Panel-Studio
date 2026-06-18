import type { PanelMember } from '../types/discussion';
import type { ExpertStatus } from '../types/expert';
import { expertStatusLabel } from '../utils/format';

interface ExpertStatusPanelProps {
  members: PanelMember[];
  statuses: Record<string, ExpertStatus>;
  compact?: boolean;
}

const statusColors: Record<string, string> = {
  idle: 'var(--color-studio-fg-subtle)',
  preparing: 'var(--color-studio-warning)',
  speaking: 'var(--color-studio-info)',
};

export function ExpertStatusPanel({ members, statuses, compact = false }: ExpertStatusPanelProps) {
  if (members.length === 0) {
    return (
      <p className="text-xs text-[var(--color-studio-fg-muted)] text-center py-4">
        暂无嘉宾
      </p>
    );
  }

  return (
    <div className={`flex ${compact ? 'flex-row gap-2' : 'flex-col gap-2'}`}>
      {members.map((member) => {
        const status = statuses[member.id];
        const currentStatus = status?.status || 'idle';

        return (
          <div
            key={member.id}
            className={`bg-[var(--color-studio-bg)] border border-[var(--color-studio-border)]
              rounded-lg transition-all duration-300
              ${currentStatus === 'speaking' ? 'animate-pulse-glow border-[var(--color-studio-info)]/50' : ''}
              ${compact ? 'flex-shrink-0 w-[200px] p-2.5' : 'p-3'}`}
          >
            {/* top row: name + status */}
            <div className="flex items-center justify-between gap-2 mb-1.5">
              <div className="flex items-center gap-2 min-w-0">
                <div
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: member.color }}
                />
                <span className="text-xs font-semibold text-[var(--color-studio-fg)] truncate">
                  {member.name}
                </span>
                {member.role === 'host' && (
                  <span className="text-[10px] text-[var(--color-studio-gold)] shrink-0">主持</span>
                )}
              </div>
              <span
                className="text-[10px] font-medium shrink-0"
                style={{ color: statusColors[currentStatus] }}
              >
                {expertStatusLabel(currentStatus)}
              </span>
            </div>

            {/* summary */}
            {status?.focusSummary && (
              <p className="text-[11px] text-[var(--color-studio-fg-muted)] leading-snug line-clamp-2">
                {status.focusSummary}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
