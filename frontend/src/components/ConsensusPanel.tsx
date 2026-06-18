import type { ConsensusItemDisplay } from '../types/consensus';
import { ConsensusItem } from './ConsensusItem';
import { EmptyState } from './EmptyState';

interface ConsensusPanelProps {
  items: ConsensusItemDisplay[];
}

export function ConsensusPanel({ items }: ConsensusPanelProps) {
  if (items.length === 0) {
    return (
      <EmptyState
        title="暂无共识或分歧"
        description="随着讨论推进，观察员将实时提炼共识与分歧"
      />
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {items.map((item) => (
        <ConsensusItem key={item.id} item={item} />
      ))}
    </div>
  );
}
