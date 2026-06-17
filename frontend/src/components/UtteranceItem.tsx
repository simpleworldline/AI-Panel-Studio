import type { UtteranceDisplay } from '../store/useStudioStore';
import { formatTime } from '../utils/format';

interface UtteranceItemProps {
  utterance: UtteranceDisplay;
}

const typeLabels: Record<string, string> = {
  opening: '开场',
  statement: '发言',
  rebuttal: '反驳',
  supplement: '补充',
  question: '提问',
  summary: '总结',
};

export function UtteranceItem({ utterance }: UtteranceItemProps) {
  const isSummary = utterance.utteranceType === 'summary';

  return (
    <div
      className={`flex gap-3 px-4 py-3.5 rounded-[var(--radius-sm)] transition-colors duration-200 hover:bg-white/[0.02] ${isSummary ? 'border-2 border-[var(--color-studio-accent)] rounded-[var(--radius-md)]' : ''}`}
      style={{ animation: 'fade-in-up 0.35s ease-out' }}
    >
      {/* Color Marker */}
      <div
        className="w-[3px] rounded-[2px] flex-shrink-0 self-stretch"
        style={{ backgroundColor: utterance.memberColor }}
      />

      <div className="flex-1 min-w-0">
        {/* Speaker info */}
        <div className="flex items-center gap-2 mb-1">
          <span className="font-semibold text-sm" style={{ color: utterance.memberColor }}>
            {utterance.memberName}
          </span>
          <span className="text-[11px] text-[var(--color-studio-fg-dim)]">{utterance.memberTitle}</span>
          <span className="text-[10px] font-semibold tracking-wider uppercase px-[6px] py-[1px] rounded-[3px] bg-white/5 text-[var(--color-studio-fg-dim)]">
            {typeLabels[utterance.utteranceType] || utterance.utteranceType}
          </span>
        </div>

        {/* Content */}
        <p className="text-sm leading-relaxed text-[var(--color-studio-fg)]">{utterance.content}</p>

        {/* Time */}
        <div className="mt-1.5 text-[10px] text-[var(--color-studio-fg-dim)] font-[var(--font-heading)]">
          {formatTime(utterance.createdAt)} · #{utterance.id.slice(0, 4)}
        </div>
      </div>
    </div>
  );
}
