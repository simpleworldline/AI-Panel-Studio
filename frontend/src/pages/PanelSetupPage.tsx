import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDiscussionStore } from '../store/useDiscussionStore';
import { usePanelStore } from '../store/usePanelStore';
import { useToastStore } from '../store/useToastStore';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';
import { Spinner } from '../components/ui/Spinner';
import { ColorPicker } from '../components/ui/ColorPicker';
import type { PanelMemberEditable } from '../types/discussion';

export function PanelSetupPage() {
  const { discussionId } = useParams<{ discussionId: string }>();
  const navigate = useNavigate();
  const { fetchDetail, currentDiscussion } = useDiscussionStore();
  const {
    host,
    experts,
    generatePhase,
    generateError,
    confirmPhase,
    confirmError,
    init,
    generate,
    updateHost,
    updateExpert,
    confirm,
    regenerateAll,
  } = usePanelStore();
  const addToast = useToastStore((s) => s.addToast);

  const [editTarget, setEditTarget] = useState<{ type: 'host' } | { type: 'expert'; index: number } | null>(null);

  useEffect(() => {
    if (discussionId) {
      fetchDetail(discussionId).then(() => {
        const detail = useDiscussionStore.getState().currentDiscussion;
        if (detail) {
          init(discussionId, detail.expertCount);
          // auto-trigger generation
          generate();
        }
      });
    }
    return () => {
      // guard: dirty check (simplified)
    };
  }, [discussionId]);

  // Redirect after confirm success
  useEffect(() => {
    if (confirmPhase === 'success' && discussionId) {
      navigate(`/studio/${discussionId}`);
    }
  }, [confirmPhase, discussionId, navigate]);

  const handleConfirm = async () => {
    await confirm();
    if (usePanelStore.getState().confirmPhase === 'error') {
      addToast({ type: 'error', message: usePanelStore.getState().confirmError || '确认失败' });
    }
  };

  if (generatePhase === 'loading' || !host) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <Spinner size="lg" />
          <p className="mt-4 text-[var(--color-studio-fg-muted)]">正在生成嘉宾阵容...</p>
        </div>
      </div>
    );
  }

  if (generatePhase === 'error') {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <p className="text-[var(--color-studio-destructive)] mb-4">{generateError || '生成失败'}</p>
          <Button variant="primary" onClick={generate}>重试</Button>
        </div>
      </div>
    );
  }

  const editData = editTarget
    ? editTarget.type === 'host'
      ? host
      : experts[editTarget.index]
    : null;

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-[720px] mx-auto px-6 py-8">
        <h1 className="font-[var(--font-heading)] text-xl font-bold mb-2">编辑嘉宾阵容</h1>
        <p className="text-sm text-[var(--color-studio-fg-muted)] mb-8">
          点击嘉宾卡片编辑信息，或点击"重新生成"更换阵容。确认后不可再编辑。
        </p>

        {/* Host */}
        <section className="mb-8">
          <h2 className="font-[var(--font-heading)] text-sm font-semibold uppercase tracking-wider text-[var(--color-studio-fg-muted)] mb-3">
            🎤 主持人
          </h2>
          <MemberEditCard
            member={host}
            onEdit={() => setEditTarget({ type: 'host' })}
            onRegenerate={() => {}}
            host
          />
        </section>

        {/* Experts */}
        <section className="mb-8">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-[var(--font-heading)] text-sm font-semibold uppercase tracking-wider text-[var(--color-studio-fg-muted)]">
              👥 专家 ({experts.length} 位)
            </h2>
            <Button variant="ghost" size="sm" onClick={() => regenerateAll()}>
              全部重新生成
            </Button>
          </div>
          <div className="flex flex-col gap-3">
            {experts.map((expert, i) => (
              <MemberEditCard
                key={i}
                member={expert}
                onEdit={() => setEditTarget({ type: 'expert', index: i })}
                onRegenerate={() => {}} // single regen not supported in current API
              />
            ))}
          </div>
        </section>

        {/* Confirm */}
        <div className="flex justify-center sticky bottom-4">
          <Button
            variant="primary"
            size="md"
            loading={confirmPhase === 'loading'}
            onClick={handleConfirm}
          >
            确认阵容，进入演播厅 →
          </Button>
        </div>
      </div>

      {/* Edit Modal */}
      <Modal
        open={!!editTarget}
        onClose={() => setEditTarget(null)}
        title="编辑嘉宾信息"
        footer={
          <Button variant="primary" onClick={() => setEditTarget(null)}>
            完成
          </Button>
        }
      >
        {editData && (
          <div className="flex flex-col gap-4">
            <div>
              <label className="block text-xs font-semibold text-[var(--color-studio-fg-muted)] uppercase tracking-wider mb-1.5">姓名</label>
              <Input
                value={editData.name}
                onChange={(v) => {
                  if (editTarget?.type === 'host') updateHost('name', v);
                  else if (editTarget?.type === 'expert') updateExpert(editTarget.index, 'name', v);
                }}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[var(--color-studio-fg-muted)] uppercase tracking-wider mb-1.5">职业 / Title</label>
              <Input
                value={editData.title}
                onChange={(v) => {
                  if (editTarget?.type === 'host') updateHost('title', v);
                  else if (editTarget?.type === 'expert') updateExpert(editTarget.index, 'title', v);
                }}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[var(--color-studio-fg-muted)] uppercase tracking-wider mb-1.5">立场描述</label>
              <Input
                value={editData.stance}
                onChange={(v) => {
                  if (editTarget?.type === 'host') updateHost('stance', v);
                  else if (editTarget?.type === 'expert') updateExpert(editTarget.index, 'stance', v);
                }}
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-[var(--color-studio-fg-muted)] uppercase tracking-wider mb-1.5">专属颜色</label>
              <ColorPicker
                value={editData.color}
                onChange={(v) => {
                  if (editTarget?.type === 'host') updateHost('color', v);
                  else if (editTarget?.type === 'expert') updateExpert(editTarget.index, 'color', v);
                }}
              />
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

// ── Inline Edit Card ──

interface MemberEditCardProps {
  member: PanelMemberEditable;
  onEdit: () => void;
  onRegenerate: () => void;
  host?: boolean;
}

function MemberEditCard({ member, onEdit, host }: MemberEditCardProps) {
  return (
    <div
      className="flex items-center gap-4 p-4 bg-[var(--color-studio-card)] border border-[var(--color-studio-border-light)] rounded-[var(--radius-md)] cursor-pointer transition-all duration-200 hover:border-[var(--color-studio-fg-dim)]"
      onClick={onEdit}
    >
      <div
        className="w-10 h-10 rounded-full flex items-center justify-center font-[var(--font-heading)] font-bold text-white text-sm flex-shrink-0"
        style={{ backgroundColor: member.color }}
      >
        {member.name.charAt(0)}
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-semibold text-sm" style={{ color: member.color }}>
          {host ? '🎤 ' : ''}{member.name}
        </div>
        <div className="text-xs text-[var(--color-studio-fg-muted)] truncate">{member.title}</div>
        <div className="text-[11px] text-[var(--color-studio-fg-dim)] italic mt-1 truncate">{member.stance}</div>
      </div>
      <div
        className="w-3 h-3 rounded-full border-2 border-white/20 flex-shrink-0"
        style={{ backgroundColor: member.color }}
      />
      <span className="text-[var(--color-studio-fg-dim)] text-sm flex-shrink-0">编辑 →</span>
    </div>
  );
}
