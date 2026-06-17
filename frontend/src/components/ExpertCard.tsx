import type { PanelMember } from '../types/discussion';
import type { ExpertStatus } from '../types/expert';
import { Badge } from './ui/Badge';

interface ExpertCardProps {
  member: PanelMember;
  status?: ExpertStatus;
  compact?: boolean;
}

export function ExpertCard({ member, status, compact = false }: ExpertCardProps) {
  const st = status?.status || 'idle';
  const isSpeaking = st === 'speaking';

  return (
    <div
      className={`bg-[var(--color-studio-card)] border border-[var(--color-studio-border-light)] rounded-[var(--radius-md)] p-3 transition-all duration-250 cursor-pointer relative overflow-hidden ${isSpeaking ? 'border-l-[5px]' : 'border-l-[3px]'}`}
      style={{
        borderLeftColor: member.color,
        '--member-glow': member.color,
      } as React.CSSProperties}
    >
      {/* Header */}
      <div className="flex items-center gap-2.5 mb-2">
        <div
          className="w-[38px] h-[38px] rounded-full flex items-center justify-center font-[var(--font-heading)] font-bold text-sm text-white flex-shrink-0"
          style={{ backgroundColor: member.color }}
        >
          {member.name.charAt(0)}
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-sm leading-tight" style={{ color: member.color }}>
            {member.name}
          </div>
          <div className="text-[11px] text-[var(--color-studio-fg-muted)] leading-tight truncate">
            {member.role === 'host' ? '🎤 ' : ''}{member.title}
          </div>
        </div>
      </div>

      {!compact && (
        <>
          {/* Stance */}
          <p className="text-[11px] text-[var(--color-studio-fg-dim)] italic leading-relaxed mb-2">
            {member.stance}
          </p>

          {/* Status Badge */}
          <Badge variant={st} />

          {/* Focus Summary */}
          {status?.focusSummary && (
            <div className="mt-2 p-2 bg-white/[0.03] rounded-[var(--radius-sm)] text-[11px] text-[var(--color-studio-fg-muted)] leading-relaxed border-l-2 border-[var(--color-studio-border)]">
              💭 {status.focusSummary}
            </div>
          )}

          {/* Desire Meter (experts only) */}
          {member.role === 'expert' && status && (
            <div className="mt-2 flex items-center gap-2">
              <div className="flex-1 h-[3px] bg-[var(--color-studio-border)] rounded-[2px] overflow-hidden">
                <div
                  className="h-full rounded-[2px] transition-[width] duration-400 ease-out"
                  style={{
                    width: `${Math.round(status.desireValue * 100)}%`,
                    backgroundColor: member.color,
                  }}
                />
              </div>
              <span className="font-[var(--font-heading)] text-[11px] text-[var(--color-studio-fg-dim)] min-w-[32px] text-right">
                {Math.round(status.desireValue * 100)}
              </span>
            </div>
          )}
        </>
      )}
    </div>
  );
}
