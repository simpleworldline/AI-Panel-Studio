import { useNavigate } from 'react-router-dom';
import type { DiscussionSummary } from '../types/discussion';
import { formatRelative, statusLabel } from '../utils/format';

interface DiscussionCardProps {
  discussion: DiscussionSummary;
}

const statusDot: Record<string, string> = {
  live: 'bg-[var(--color-studio-success)]',
  paused: 'bg-[var(--color-studio-warning)]',
  ended: 'bg-[var(--color-studio-fg-subtle)]',
};

export function DiscussionCard({ discussion }: DiscussionCardProps) {
  const navigate = useNavigate();
  const isLive = discussion.status === 'live' || discussion.status === 'paused';

  const handleClick = () => {
    if (isLive) {
      navigate(`/studio/${discussion.id}`);
    } else {
      navigate(`/report/${discussion.id}`);
    }
  };

  return (
    <div
      onClick={handleClick}
      className="p-4 bg-[var(--color-studio-card)] border border-[var(--color-studio-border)]
        rounded-xl hover:border-[var(--color-studio-info)]/40 transition-all duration-200
        cursor-pointer group"
    >
      {/* top row */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <h3 className="text-sm font-semibold text-[var(--color-studio-fg)] leading-snug line-clamp-2
          group-hover:text-[var(--color-studio-info)] transition-colors">
          {discussion.topic}
        </h3>
        <span className={`shrink-0 flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px]
          ${discussion.status === 'live' ? 'bg-[var(--color-studio-consensus-dim)]/30 text-[var(--color-studio-consensus)]' : ''}
          ${discussion.status === 'paused' ? 'bg-[var(--color-studio-warning)]/20 text-[var(--color-studio-warning)]' : ''}
          ${discussion.status === 'ended' ? 'bg-[var(--color-studio-fg-subtle)]/20 text-[var(--color-studio-fg-muted)]' : ''}`}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${statusDot[discussion.status] || ''}`} />
          {statusLabel(discussion.status)}
        </span>
      </div>

      {/* preview */}
      {discussion.memberPreview && discussion.memberPreview.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {discussion.memberPreview.slice(0, 4).map((m, i) => (
            <span key={i} className="text-[11px] text-[var(--color-studio-fg-muted)]">
              {m.name}{i < Math.min(discussion.memberPreview.length, 4) - 1 ? '、' : ''}
            </span>
          ))}
        </div>
      )}

      {/* bottom meta */}
      <div className="flex items-center gap-3 text-[11px] text-[var(--color-studio-fg-subtle)]">
        <span>{discussion.expertCount} 位嘉宾</span>
        {discussion.currentRound > 0 && <span>第 {discussion.currentRound} 轮</span>}
        <span className="ml-auto">{formatRelative(discussion.createdAt)}</span>
      </div>
    </div>
  );
}
