import type { UtteranceDisplay } from '../store/useStudioStore';
import { formatTime, utteranceTypeLabel } from '../utils/format';

interface UtteranceItemProps {
  utterance: UtteranceDisplay;
}

export function UtteranceItem({ utterance }: UtteranceItemProps) {
  return (
    <div className="flex gap-3 px-4 py-3 animate-fade-in">
      {/* avatar dot */}
      <div
        className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0 mt-0.5"
        style={{ backgroundColor: utterance.memberColor }}
      >
        {utterance.memberName.charAt(0)}
      </div>

      {/* content */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-semibold" style={{ color: utterance.memberColor }}>
            {utterance.memberName}
          </span>
          <span className="text-[10px] text-[var(--color-studio-fg-subtle)]">
            {utterance.memberTitle}
          </span>
          <span
            className="text-[10px] px-1.5 py-0.5 rounded"
            style={{ backgroundColor: utterance.memberColor + '18', color: utterance.memberColor }}
          >
            {utteranceTypeLabel(utterance.utteranceType)}
          </span>
          <span className="text-[10px] text-[var(--color-studio-fg-subtle)] ml-auto">
            {formatTime(utterance.createdAt)}
          </span>
        </div>
        <p className="text-sm text-[var(--color-studio-fg)] leading-relaxed whitespace-pre-wrap break-words">
          {utterance.content}
        </p>
      </div>
    </div>
  );
}
