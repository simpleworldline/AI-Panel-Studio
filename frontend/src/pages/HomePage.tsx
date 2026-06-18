import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDiscussionStore } from '../store/useDiscussionStore';
import { DiscussionCard } from '../components/DiscussionCard';
import { Spinner } from '../components/ui/Spinner';
import { Button } from '../components/ui/Button';
import { EmptyState } from '../components/EmptyState';

export function HomePage() {
  const navigate = useNavigate();
  const { discussions, listLoading, listError, activeTab, fetchList, setActiveTab } = useDiscussionStore();

  useEffect(() => {
    fetchList(activeTab);
  }, [activeTab]);

  return (
    <div className="flex-1 flex flex-col max-w-5xl mx-auto w-full px-4 py-6 overflow-hidden">
      {/* Fixed header: hero + tabs */}
      <div className="shrink-0">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-[var(--color-studio-fg)] mb-2">AI 演播厅</h1>
          <p className="text-sm text-[var(--color-studio-fg-muted)] max-w-md mx-auto">
            输入话题，AI 自动生成嘉宾阵容，观看一场由 AI 驱动的圆桌讨论
          </p>
          <div className="mt-5">
            <Button variant="primary" size="lg" onClick={() => navigate('/create')}>
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 5v14M5 12h14" />
              </svg>
              发起新讨论
            </Button>
          </div>
        </div>

        <div className="flex items-center gap-1 mb-4 p-0.5 rounded-lg bg-[var(--color-studio-bg)]
          border border-[var(--color-studio-border)] w-fit">
          {(['live', 'pending', 'ended'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-1.5 text-xs font-medium rounded-md transition-all duration-150 cursor-pointer
                ${activeTab === tab ? 'bg-[var(--color-studio-elevated)] text-[var(--color-studio-fg)] shadow-sm'
                : 'text-[var(--color-studio-fg-muted)] hover:text-[var(--color-studio-fg)]'}`}
            >
              {{ live: '进行中', pending: '待开始', ended: '已结束' }[tab]}
            </button>
          ))}
        </div>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto">
        {listLoading ? (
          <div className="flex-1 flex items-center justify-center py-20">
            <Spinner size="lg" />
          </div>
        ) : listError ? (
          <div className="flex-1 flex items-center justify-center py-20">
            <div className="text-center">
              <p className="text-sm text-[var(--color-studio-destructive)] mb-3">{listError}</p>
              <Button variant="secondary" size="sm" onClick={() => fetchList(activeTab)}>重试</Button>
            </div>
          </div>
        ) : discussions.length === 0 ? (
          <div className="py-20">
            <EmptyState
              title={
                activeTab === 'live' ? '暂无进行中的讨论' :
                activeTab === 'pending' ? '暂无待开始的讨论' :
                '暂无已结束的讨论'
              }
              description={
                activeTab === 'live' ? '发起一个新讨论，成为第一位主持人' :
                activeTab === 'pending' ? '创建讨论后，它将出现在这里' :
                '完成一场讨论后，它将出现在这里'
              }
              icon={
                <svg className="w-12 h-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a2 2 0 01-2-2v-3" />
                  <path d="M3 3h10a2 2 0 012 2v8a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2z" />
                </svg>
              }
            />
          </div>
        ) : (
          <div className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 pb-6">
            {discussions.map((d) => (
              <DiscussionCard key={d.id} discussion={d} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
