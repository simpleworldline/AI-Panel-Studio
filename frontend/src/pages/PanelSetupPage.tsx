import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { usePanelStore } from '../store/usePanelStore';
import { useToastStore } from '../store/useToastStore';
import { MemberCard } from '../components/MemberCard';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { ColorPicker } from '../components/ui/ColorPicker';
import { Modal } from '../components/ui/Modal';
import { Spinner } from '../components/ui/Spinner';
import type { PanelMember } from '../types/discussion';

export function PanelSetupPage() {
  const { discussionId } = useParams<{ discussionId: string }>();
  const navigate = useNavigate();
  const store = usePanelStore();
  const addToast = useToastStore((s) => s.addToast);

  const [editingExpert, setEditingExpert] = useState<number | null>(null);
  const [editingHost, setEditingHost] = useState(false);

  useEffect(() => {
    if (!discussionId) return;
    store.init(discussionId, 4);
    store.generate(discussionId);
    return () => { store.reset(); };
  }, [discussionId]);

  const handleConfirm = async () => {
    if (!discussionId || !store.host) return;
    try {
      await store.confirm(discussionId);
      addToast({ type: 'success', message: '嘉宾阵容确认成功' });
      navigate(`/studio/${discussionId}`);
    } catch {
      addToast({ type: 'error', message: store.confirmError || '确认失败' });
    }
  };

  if (!discussionId) return null;

  return (
    <div className="flex-1 flex flex-col max-w-3xl mx-auto w-full px-4 py-6">
      {/* header */}
      <div className="text-center mb-6">
        <h1 className="text-xl font-bold text-[var(--color-studio-fg)] mb-2">嘉宾阵容</h1>
        <p className="text-sm text-[var(--color-studio-fg-muted)]">
          编辑嘉宾信息，或重新生成不满意的人选
        </p>
      </div>

      {/* loading */}
      {store.generating && !store.host ? (
        <div className="flex-1 flex flex-col items-center justify-center gap-3">
          <Spinner size="lg" />
          <p className="text-sm text-[var(--color-studio-fg-muted)]">AI 正在生成嘉宾阵容…</p>
        </div>
      ) : store.generateError ? (
        <div className="text-center">
          <p className="text-sm text-[var(--color-studio-destructive)] mb-3">{store.generateError}</p>
          <Button variant="secondary" onClick={() => store.generate(discussionId)}>重试</Button>
        </div>
      ) : (
        <>
          {/* host */}
          {store.host && (
            <div className="mb-6">
              <h2 className="text-sm font-semibold text-[var(--color-studio-gold)] mb-2 flex items-center gap-2">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 2L2 7l10 5 10-5-10-5z" />
                </svg>
                主持人
              </h2>
              <MemberCard
                member={{ ...store.host, id: 'host', role: 'host', avatarPrompt: '' } as PanelMember}
                onEdit={() => setEditingHost(true)}
                onRegenerate={() => store.generate(discussionId)}
                showActions
              />
            </div>
          )}

          {/* experts */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-sm font-semibold text-[var(--color-studio-fg)] flex items-center gap-2">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="8" r="4" />
                  <path d="M6 21v-2a4 4 0 014-4h4a4 4 0 014 4v2" />
                </svg>
                嘉宾 ({store.experts.length} 位)
              </h2>
              <Button
                variant="ghost"
                size="sm"
                loading={store.generating}
                onClick={() => store.regenerateAll(discussionId)}
              >
                全部重新生成
              </Button>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              {store.experts.map((expert, i) => (
                <MemberCard
                  key={i}
                  member={{ ...expert, id: `expert-${i}`, role: 'expert', avatarPrompt: '' } as PanelMember}
                  onEdit={() => setEditingExpert(i)}
                  onRegenerate={() => store.regenerateOne(discussionId, i)}
                  showActions
                />
              ))}
            </div>
          </div>

          {/* confirm */}
          <div className="sticky bottom-0 py-4 bg-[var(--color-studio-bg)] border-t border-[var(--color-studio-border)]">
            <Button
              variant="primary"
              size="lg"
              className="w-full"
              loading={store.confirming}
              onClick={handleConfirm}
            >
              确认阵容，进入演播厅
            </Button>
          </div>
        </>
      )}

      {/* Edit Host Modal */}
      {store.host && (
        <Modal
          open={editingHost}
          onClose={() => setEditingHost(false)}
          title="编辑主持人"
          footer={
            <Button variant="primary" size="sm" onClick={() => setEditingHost(false)}>
              完成
            </Button>
          }
        >
          <div className="flex flex-col gap-3">
            <Input label="姓名" value={store.host.name} onChange={(e) => store.updateHost({ name: e.target.value })} />
            <Input label="Title / 职业" value={store.host.title} onChange={(e) => store.updateHost({ title: e.target.value })} />
            <Input label="立场" value={store.host.stance} onChange={(e) => store.updateHost({ stance: e.target.value })} />
            <ColorPicker value={store.host.color} onChange={(c) => store.updateHost({ color: c })} />
          </div>
        </Modal>
      )}

      {/* Edit Expert Modal */}
      {editingExpert !== null && store.experts[editingExpert] && (
        <Modal
          open={editingExpert !== null}
          onClose={() => setEditingExpert(null)}
          title={`编辑嘉宾 — ${store.experts[editingExpert].name}`}
          footer={
            <Button variant="primary" size="sm" onClick={() => setEditingExpert(null)}>
              完成
            </Button>
          }
        >
          <div className="flex flex-col gap-3">
            <Input label="姓名" value={store.experts[editingExpert].name} onChange={(e) => store.updateExpert(editingExpert, { name: e.target.value })} />
            <Input label="Title / 职业" value={store.experts[editingExpert].title} onChange={(e) => store.updateExpert(editingExpert, { title: e.target.value })} />
            <Input label="立场" value={store.experts[editingExpert].stance} onChange={(e) => store.updateExpert(editingExpert, { stance: e.target.value })} />
            <ColorPicker value={store.experts[editingExpert].color} onChange={(c) => store.updateExpert(editingExpert, { color: c })} />
          </div>
        </Modal>
      )}
    </div>
  );
}
