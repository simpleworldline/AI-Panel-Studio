import type { PanelMember } from '../types/discussion';

interface MemberCardProps {
  member: PanelMember;
  onEdit?: () => void;
  onRegenerate?: () => void;
  showActions?: boolean;
}

export function MemberCard({ member, onEdit, onRegenerate, showActions = false }: MemberCardProps) {
  return (
    <div
      className="p-4 bg-[var(--color-studio-card)] border border-[var(--color-studio-border)]
        rounded-xl transition-all duration-200"
      style={{ borderLeftColor: member.color, borderLeftWidth: '3px' }}
    >
      {/* header */}
      <div className="flex items-center gap-2.5 mb-2">
        <div
          className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white shrink-0"
          style={{ backgroundColor: member.color }}
        >
          {member.name.charAt(0)}
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="text-sm font-semibold text-[var(--color-studio-fg)] truncate">
              {member.name}
            </span>
            <span
              className="text-[10px] px-1.5 py-0.5 rounded font-medium"
              style={{ backgroundColor: member.color + '20', color: member.color }}
            >
              {member.role === 'host' ? '主持人' : '嘉宾'}
            </span>
          </div>
          <p className="text-xs text-[var(--color-studio-fg-muted)] truncate">{member.title}</p>
        </div>
      </div>

      {/* stance */}
      <p className="text-xs text-[var(--color-studio-fg-subtle)] leading-relaxed line-clamp-2">
        {member.stance}
      </p>

      {/* actions */}
      {showActions && (
        <div className="flex items-center gap-2 mt-3 pt-3 border-t border-[var(--color-studio-border)]">
          {onEdit && (
            <button
              onClick={onEdit}
              className="text-xs text-[var(--color-studio-info)] hover:underline cursor-pointer transition-colors"
            >
              编辑
            </button>
          )}
          {onRegenerate && (
            <button
              onClick={onRegenerate}
              className="text-xs text-[var(--color-studio-fg-muted)] hover:text-[var(--color-studio-fg)] cursor-pointer transition-colors"
            >
              重新生成
            </button>
          )}
        </div>
      )}
    </div>
  );
}
