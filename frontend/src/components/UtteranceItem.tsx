import type { UtteranceDisplay } from '../store/useStudioStore';
import { formatTime } from '../utils/format';

interface UtteranceItemProps {
  utterance: UtteranceDisplay;
  isChild?: boolean;
}

const typeBadgeStyle: Record<string, { bg: string; fg: string; label: string }> = {
  statement:  { bg: 'var(--color-studio-border)', fg: 'var(--color-studio-fg-muted)', label: '发言' },
  question:   { bg: 'rgba(240,192,96,0.15)', fg: 'var(--color-studio-gold)', label: '追问' },
  opening:    { bg: 'rgba(240,192,96,0.15)', fg: 'var(--color-studio-gold)', label: '开场' },
  summary:    { bg: 'rgba(99,102,241,0.15)', fg: 'var(--color-studio-info)', label: '总结' },
};

export function UtteranceItem({ utterance, isChild = false }: UtteranceItemProps) {
  const badge = typeBadgeStyle[utterance.utteranceType] || typeBadgeStyle.statement;

  return (
    <div className={`flex gap-3 px-4 py-3 animate-fade-in ${isChild ? '' : ''}`}>
      {/* avatar dot */}
      <div
        className={`rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0 mt-0.5
          ${isChild ? 'w-6 h-6 text-[10px]' : 'w-8 h-8'}`}
        style={{ backgroundColor: utterance.memberColor }}
      >
        {utterance.memberName.charAt(0)}
      </div>

      {/* content */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className={`font-semibold ${isChild ? 'text-xs' : 'text-xs'}`} style={{ color: utterance.memberColor }}>
            {utterance.memberName}
          </span>
          <span className={`text-[var(--color-studio-fg-subtle)] ${isChild ? 'text-[9px]' : 'text-[10px]'}`}>
            {utterance.memberTitle}
          </span>
          <span
            className="px-1.5 py-0.5 rounded text-[10px] font-medium"
            style={{ backgroundColor: badge.bg, color: badge.fg }}
          >
            {badge.label}
          </span>
          <span className={`text-[var(--color-studio-fg-subtle)] ml-auto ${isChild ? 'text-[9px]' : 'text-[10px]'}`}>
            {formatTime(utterance.createdAt)}
          </span>
        </div>
        <p className={`text-[var(--color-studio-fg)] leading-relaxed whitespace-pre-wrap break-words ${isChild ? 'text-xs' : 'text-sm'}`}>
          {utterance.content}
        </p>
      </div>
    </div>
  );
}
