import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDiscussionStore } from '../store/useDiscussionStore';
import { UtteranceItem } from '../components/UtteranceItem';
import { ConsensusPanel } from '../components/ConsensusPanel';
import { Spinner } from '../components/ui/Spinner';
import { Button } from '../components/ui/Button';
import type { UtteranceDisplay } from '../store/useStudioStore';

export function ReportPage() {
  const { discussionId } = useParams<{ discussionId: string }>();
  const navigate = useNavigate();
  const { currentDiscussion, detailLoading, detailError, fetchDetail, clearCurrent } =
    useDiscussionStore();

  useEffect(() => {
    if (!discussionId) return;
    clearCurrent();
    fetchDetail(discussionId);
    return () => clearCurrent();
  }, [discussionId]);

  if (detailLoading || !currentDiscussion) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (detailError) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <p className="text-sm text-[var(--color-studio-destructive)] mb-4">{detailError}</p>
          <Button variant="primary" onClick={() => navigate('/')}>返回首页</Button>
        </div>
      </div>
    );
  }

  const utterances: UtteranceDisplay[] = (currentDiscussion.transcript || []).map((u: any) => ({
    id: u.id,
    panelMemberId: u.panelMemberId || u.panel_member_id || '',
    memberName: u.memberName || u.member_name || '',
    memberTitle: u.memberTitle || u.member_title || '',
    memberColor: u.memberColor || u.member_color || '',
    content: u.content,
    utteranceType: u.utteranceType || u.utterance_type || '',
    sequenceNum: u.sequenceNum || u.sequence_num || 0,
    roundNum: u.roundNum || u.round_num || 0,
    createdAt: u.createdAt || u.created_at || '',
  }));

  const consensus = (currentDiscussion.consensus || []).map((c: any) => ({
    ...c,
    type: 'consensus' as const,
  }));
  const disagreements = (currentDiscussion.disagreements || []).map((d: any) => ({
    ...d,
    type: 'disagreement' as const,
  }));
  const allConsensus = [...consensus, ...disagreements];

  return (
    <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full px-4 py-6 overflow-y-auto">
      {/* header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <Button variant="ghost" size="sm" onClick={() => navigate('/')}>
            ← 返回首页
          </Button>
          <span className="text-xs text-[var(--color-studio-fg-muted)]">
            {currentDiscussion.status === 'ended' ? '已结束' : '进行中'}
          </span>
        </div>
        <h1 className="text-xl font-bold text-[var(--color-studio-fg)] mb-2">
          {currentDiscussion.topic}
        </h1>
        <div className="flex items-center gap-3 text-xs text-[var(--color-studio-fg-muted)]">
          <span>{currentDiscussion.expertCount} 位嘉宾</span>
          <span>共 {utterances.length} 条发言</span>
          <span>第 {currentDiscussion.currentRound} 轮</span>
        </div>
      </div>

      {/* Transcript */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-[var(--color-studio-fg)] mb-3 flex items-center gap-2">
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
          </svg>
          讨论记录
        </h2>
        <div className="bg-[var(--color-studio-card)] border border-[var(--color-studio-border)] rounded-xl divide-y divide-[var(--color-studio-border)]">
          {utterances.map((u) => (
            <UtteranceItem key={u.id} utterance={u} />
          ))}
        </div>
      </section>

      {/* Consensus */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-[var(--color-studio-fg)] mb-3 flex items-center gap-2">
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2" />
            <rect x="9" y="3" width="6" height="4" rx="1" />
          </svg>
          共识与分歧
        </h2>
        {allConsensus.length === 0 ? (
          <p className="text-sm text-[var(--color-studio-fg-muted)] py-6 text-center">
            暂无共识或分歧记录
          </p>
        ) : (
          <ConsensusPanel items={allConsensus} />
        )}
      </section>
    </div>
  );
}
