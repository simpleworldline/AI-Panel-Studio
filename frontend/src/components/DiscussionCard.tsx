import { useNavigate } from 'react-router-dom';
import type { DiscussionSummary } from '../types/discussion';
import { Badge } from './ui/Badge';
import { PanelDots } from './PanelDots';
import { formatRelativeTime } from '../utils/format';

interface DiscussionCardProps {
  discussion: DiscussionSummary;
}

export function DiscussionCard({ discussion }: DiscussionCardProps) {
  const navigate = useNavigate();
  const isLive = discussion.status === 'live';

  const handleClick = () => {
    const path = isLive
      ? `/studio/${discussion.id}`
      : `/report/${discussion.id}`;
    navigate(path);
  };

  return (
    <div
      className="flex items-center gap-4 p-[18px] bg-[var(--color-studio-card)] border border-[var(--color-studio-border-light)] rounded-[var(--radius-md)] cursor-pointer transition-all duration-200 hover:border-[var(--color-studio-fg-dim)] hover:bg-[var(--color-studio-hover)] hover:translate-x-[3px] relative overflow-hidden"
      tabIndex={0}
      role="button"
      aria-label={discussion.topic}
      onClick={handleClick}
      onKeyDown={(e) => { if (e.key === 'Enter') handleClick(); }}
    >
      {/* left indicator */}
      <div
        className={`w-[3px] self-stretch rounded-[2px] flex-shrink-0 ${
          isLive
            ? 'bg-[var(--color-studio-accent)] shadow-[0_0_8px_rgba(34,197,94,0.3)]'
            : 'bg-[var(--color-studio-fg-dim)]'
        }`}
      />

      <div className="flex-1 min-w-0">
        <div className="text-base font-semibold leading-relaxed mb-1">{discussion.topic}</div>
        <div className="flex items-center gap-4 flex-wrap text-xs text-[var(--color-studio-fg-dim)]">
          <span>👥 {discussion.expertCount} 位专家</span>
          <span>🔄 第 {discussion.currentRound} 轮</span>
          <span>🕐 {formatRelativeTime(discussion.createdAt)}</span>
        </div>
        <div className="mt-2">
          <PanelDots members={discussion.memberPreview as any} />
        </div>
      </div>

      <Badge variant={isLive ? 'live' : 'ended'}>
        {isLive ? '直播中' : '已结束'}
      </Badge>

      <span className="text-[var(--color-studio-fg-dim)] text-lg flex-shrink-0 transition-transform duration-200 group-hover:translate-x-1">
        →
      </span>
    </div>
  );
}
