import type { ConsensusItemDisplay } from '../types/consensus';

interface ConsensusItemProps {
  item: ConsensusItemDisplay;
}

export function ConsensusItem({ item }: ConsensusItemProps) {
  const isConsensus = item.type === 'consensus';

  return (
    <div
      className={`p-3 rounded-lg border animate-fade-in transition-all duration-200
        ${isConsensus
          ? 'bg-[var(--color-studio-consensus-dim)]/10 border-[var(--color-studio-consensus-dim)]/30'
          : 'bg-[var(--color-studio-disagreement-dim)]/10 border-[var(--color-studio-disagreement-dim)]/30'
        }`}
    >
      {/* header */}
      <div className="flex items-center gap-2 mb-1.5">
        <span
          className={`text-[10px] font-semibold px-1.5 py-0.5 rounded
            ${isConsensus
              ? 'bg-[var(--color-studio-consensus-dim)]/20 text-[var(--color-studio-consensus)]'
              : 'bg-[var(--color-studio-disagreement-dim)]/20 text-[var(--color-studio-disagreement)]'
            }`}
        >
          {isConsensus ? '共识' : '分歧'}
        </span>
        <span className="text-xs text-[var(--color-studio-fg-muted)]">
          置信度 {Math.round(item.confidence * 100)}%
        </span>
        {item.isResolved && (
          <span className="text-[10px] text-[var(--color-studio-success)] ml-auto">
            已化解
          </span>
        )}
      </div>

      {/* title */}
      <h4 className="text-sm font-medium text-[var(--color-studio-fg)] mb-1">
        {item.title}
      </h4>

      {/* description */}
      <p className="text-xs text-[var(--color-studio-fg-muted)] leading-relaxed">
        {item.description}
      </p>
    </div>
  );
}
