import type { ConsensusRecord } from '../types/consensus';

interface ConsensusItemProps {
  item: ConsensusRecord;
}

export function ConsensusItem({ item }: ConsensusItemProps) {
  const isConsensus = item.type === 'consensus';
  const confLevel = item.confidence >= 0.8 ? 'high' : item.confidence >= 0.5 ? 'mid' : 'low';

  const confDotColor =
    confLevel === 'high'
      ? 'var(--color-consensus-green)'
      : confLevel === 'mid'
        ? 'var(--color-studio-warning)'
        : 'var(--color-studio-destructive)';

  return (
    <div
      className="bg-[var(--color-studio-card)] border border-[var(--color-studio-border-light)] rounded-[var(--radius-md)] p-3.5 cursor-pointer transition-colors duration-200 hover:border-[var(--color-studio-fg-dim)]"
      style={{ animation: 'fade-in-up 0.35s ease-out' }}
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-2">
        <span
          className={`inline-flex items-center gap-1 px-[6px] py-[2px] rounded text-[10px] font-bold tracking-wider uppercase ${
            isConsensus
              ? 'bg-[rgba(52,211,153,0.10)] text-[var(--color-consensus-green)]'
              : 'bg-[rgba(251,146,60,0.10)] text-[var(--color-consensus-orange)]'
          }`}
        >
          {isConsensus ? '✓ 共识' : '⚡ 分歧'}
        </span>
        {item.isResolved && (
          <span className="px-[6px] py-[2px] rounded text-[9px] font-bold uppercase bg-[rgba(52,211,153,0.10)] text-[var(--color-consensus-green)]">
            已化解
          </span>
        )}
      </div>

      {/* Title */}
      <div className="font-semibold text-sm leading-relaxed mb-1.5">{item.title}</div>

      {/* Description */}
      <p className="text-xs text-[var(--color-studio-fg-muted)] leading-relaxed">{item.description}</p>

      {/* Meta */}
      <div className="flex items-center justify-between mt-2.5 text-[10px] text-[var(--color-studio-fg-dim)]">
        <span className="flex items-center gap-1">
          置信度
          <span
            className="inline-block w-2 h-2 rounded-full"
            style={{ backgroundColor: confDotColor }}
          />
          {Math.round(item.confidence * 100)}%
        </span>
        <span>第 {item.roundNum} 轮</span>
      </div>
    </div>
  );
}
