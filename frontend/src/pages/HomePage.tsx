import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDiscussionStore } from '../store/useDiscussionStore';
import { DiscussionCard } from '../components/DiscussionCard';
import { EmptyState } from '../components/EmptyState';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';
import { Spinner } from '../components/ui/Spinner';

export function HomePage() {
  const navigate = useNavigate();
  const {
    liveDiscussions,
    endedDiscussions,
    listLoading,
    listError,
    fetchList,
    createNew,
  } = useDiscussionStore();

  const [activeTab, setActiveTab] = useState<'live' | 'ended'>('live');
  const [showCreate, setShowCreate] = useState(false);
  const [topic, setTopic] = useState('');
  const [expertCount, setExpertCount] = useState(4);
  const [maxRounds, setMaxRounds] = useState(0);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchList();
  }, [fetchList]);

  const handleCreate = useCallback(async () => {
    if (!topic.trim() || topic.length > 200) return;
    setCreating(true);
    try {
      const id = await createNew({
        topic: topic.trim(),
        expertCount,
        maxRounds: maxRounds > 0 ? maxRounds : null,
      });
      setShowCreate(false);
      setTopic('');
      setExpertCount(4);
      setMaxRounds(0);
      navigate(`/create/${id}/panel`);
    } catch {
      // error handled by toast in API interceptor
    } finally {
      setCreating(false);
    }
  }, [topic, expertCount, maxRounds, createNew, navigate]);

  return (
    <div className="flex-1 overflow-y-auto">
      {/* Hero */}
      <section className="text-center px-6 py-16 relative overflow-hidden">
        <div
          className="absolute inset-0 pointer-events-none -z-10"
          style={{
            background:
              'radial-gradient(ellipse 60% 50% at 50% 30%, rgba(34,197,94,0.04) 0%, transparent 70%), radial-gradient(ellipse 40% 40% at 30% 70%, rgba(99,102,241,0.03) 0%, transparent 70%), radial-gradient(ellipse 40% 40% at 70% 70%, rgba(59,130,246,0.03) 0%, transparent 70%)',
          }}
        />
        <div className="w-16 h-16 mx-auto mb-5 bg-[var(--color-studio-card)] border border-[var(--color-studio-border)] rounded-[var(--radius-lg)] flex items-center justify-center text-3xl">
          🎙️
        </div>
        <h1 className="font-[var(--font-heading)] text-[2.2rem] font-bold tracking-tight mb-3">
          观看 AI 专家的<span className="text-[var(--color-studio-accent)]">圆桌讨论</span>
        </h1>
        <p className="text-base text-[var(--color-studio-fg-muted)] max-w-[520px] mx-auto mb-7 leading-relaxed">
          输入任何话题，AI 自动生成主持人与专家阵容。观看一场去中心化、实时推进的深度圆桌讨论——共识与分歧实时呈现。
        </p>
        <Button
          variant="primary"
          size="md"
          onClick={() => setShowCreate(true)}
          iconLeft={<span>+</span>}
        >
          发起新讨论
        </Button>
        <div className="flex justify-center gap-8 mt-9">
          <div className="text-center">
            <div className="font-[var(--font-heading)] text-2xl font-bold text-[var(--color-studio-accent)]">
              {liveDiscussions.length}
            </div>
            <div className="text-[11px] text-[var(--color-studio-fg-dim)] uppercase tracking-wider mt-0.5">
              进行中
            </div>
          </div>
          <div className="text-center">
            <div className="font-[var(--font-heading)] text-2xl font-bold text-[var(--color-studio-accent)]">
              {liveDiscussions.length + endedDiscussions.length}
            </div>
            <div className="text-[11px] text-[var(--color-studio-fg-dim)] uppercase tracking-wider mt-0.5">
              总讨论数
            </div>
          </div>
        </div>
      </section>

      {/* Content */}
      <div className="max-w-[960px] mx-auto px-6 pb-16">
        {/* Tabs */}
        <div className="flex gap-0 mb-6 border-b border-[var(--color-studio-border)]">
          {(['live', 'ended'] as const).map((tab) => (
            <button
              key={tab}
              className={`py-2.5 px-5 text-sm font-medium border-b-2 transition-colors duration-200 -mb-px cursor-pointer ${
                activeTab === tab
                  ? 'text-[var(--color-studio-accent)] border-[var(--color-studio-accent)]'
                  : 'text-[var(--color-studio-fg-dim)] border-transparent hover:text-[var(--color-studio-fg-muted)]'
              }`}
              onClick={() => setActiveTab(tab)}
            >
              {tab === 'live' ? '进行中' : '已结束'}
            </button>
          ))}
        </div>

        {/* List */}
        {listLoading ? (
          <div className="flex justify-center py-16">
            <Spinner size="lg" />
          </div>
        ) : listError ? (
          <EmptyState
            icon="⚠️"
            title="加载失败"
            description={listError}
            action={{ label: '重试', onClick: fetchList }}
          />
        ) : (
          <div className="flex flex-col gap-3">
            {(activeTab === 'live' ? liveDiscussions : endedDiscussions).map((d) => (
              <DiscussionCard key={d.id} discussion={d} />
            ))}
            {(activeTab === 'live' ? liveDiscussions : endedDiscussions).length === 0 && (
              <EmptyState
                icon="📺"
                title={activeTab === 'live' ? '暂无进行中的讨论' : '暂无已结束讨论'}
                description={
                  activeTab === 'live' ? '发起一场新讨论，成为第一个话题的发起者' : undefined
                }
                action={
                  activeTab === 'live'
                    ? { label: '发起新讨论', onClick: () => setShowCreate(true) }
                    : undefined
                }
              />
            )}
          </div>
        )}
      </div>

      {/* Create Modal */}
      <Modal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        title="发起新讨论"
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowCreate(false)}>
              取消
            </Button>
            <Button
              variant="primary"
              disabled={!topic.trim() || topic.length > 200}
              loading={creating}
              onClick={handleCreate}
            >
              生成嘉宾阵容 →
            </Button>
          </>
        }
      >
        <div className="flex flex-col gap-4">
          <div>
            <label className="block text-xs font-semibold text-[var(--color-studio-fg-muted)] uppercase tracking-wider mb-1.5">
              讨论话题
            </label>
            <Input
              value={topic}
              onChange={setTopic}
              placeholder="例如：AI是否应该具备自我意识？"
              maxLength={200}
              error={topic.length > 200 ? `已超出 ${topic.length - 200} 字` : undefined}
            />
            <div className={`text-[10px] mt-1 ${topic.length > 200 ? 'text-[var(--color-studio-destructive)]' : 'text-[var(--color-studio-fg-dim)]'}`}>
              {topic.length} / 200
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--color-studio-fg-muted)] uppercase tracking-wider mb-1.5">
              专家人数
            </label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min={2}
                max={8}
                value={expertCount}
                onChange={(e) => setExpertCount(Number(e.target.value))}
                className="flex-1 accent-[var(--color-studio-accent)]"
              />
              <span className="font-[var(--font-heading)] text-lg font-bold text-[var(--color-studio-accent)] min-w-[24px]">
                {expertCount}
              </span>
            </div>
            <p className="text-[10px] text-[var(--color-studio-fg-dim)] mt-1">2-8 位专家，默认 4 人。含 1 位主持人。</p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--color-studio-fg-muted)] uppercase tracking-wider mb-1.5">
              最大轮次（可选）
            </label>
            <Input
              type="number"
              value={String(maxRounds)}
              onChange={(v) => setMaxRounds(Math.max(0, Math.min(99, Number(v) || 0)))}
              placeholder="0 = 不限"
              min={0}
              max={99}
            />
            <p className="text-[10px] text-[var(--color-studio-fg-dim)] mt-1">达到最大轮次后自动结束。设为 0 则不限制。</p>
          </div>
        </div>
      </Modal>
    </div>
  );
}
