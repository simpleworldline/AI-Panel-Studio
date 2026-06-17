import type { ConsensusRecord } from '../types/consensus';
import { ConsensusItem } from './ConsensusItem';
import { EmptyState } from './EmptyState';

interface ConsensusPanelProps {
  items: ConsensusRecord[];
}

export function ConsensusPanel({ items }: ConsensusPanelProps) {
  if (items.length === 0) {
    return (
      <EmptyState
        icon="📋"
        title="暂无共识或分歧记录"
        description="随讨论进行，此区域将实时更新"
      />
    );
  }

  return (
    <div className="flex flex-col gap-2.5">
      {items.map((c) => (
        <ConsensusItem key={c.id} item={c} />
      ))}
    </div>
  );
}
