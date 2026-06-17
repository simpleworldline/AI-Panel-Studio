import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDiscussionStore } from '../store/useDiscussionStore';
import { TranscriptView } from '../components/TranscriptView';
import { ConsensusPanel } from '../components/ConsensusPanel';
import { Spinner } from '../components/ui/Spinner';
import { Button } from '../components/ui/Button';
import { EmptyState } from '../components/EmptyState';
import type { UtteranceDisplay } from '../store/useStudioStore';

export function ReportPage() {
  const { discussionId } = useParams<{ discussionId: string }>();
  const navigate = useNavigate();
  const { currentDiscussion, detailLoading, detailError, fetchDetail, clearCurrent } = useDiscussionStore();

  useEffect(() => {
    if (discussionId) {
      fetchDetail(discussionId);
    }
    return () => clearCurrent();
  }, [discussionId]);

  if (detailLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (detailError || !currentDiscussion) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <p className="text-[var(--color-studio-destructive)] mb-4">{detailError || '讨论不存在'}</p>
          <Button variant="primary" onClick={() => navigate('/')}>返回首页</Button>
        </div>
      </div>
    );
  }

  const utterances: UtteranceDisplay[] = currentDiscussion.transcript.map((u) => ({
    id: u.id,
    panelMemberId: u.panelMemberId,
    memberName: u.memberName,
    memberTitle: u.memberTitle,
    memberColor: u.memberColor,
    content: u.content,
    utteranceType: u.utteranceType,
    sequenceNum: u.sequenceNum,
    roundNum: u.roundNum,
    createdAt: u.createdAt,
  }));

  const allConsensus = [
    ...currentDiscussion.consensus.map((c) => ({ ...c, type: 'consensus' as const })),
    ...currentDiscussion.disagreements.map((d) => ({ ...d, type: 'disagreement' as const })),
  ];

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-[720px] mx-auto px-6 py-8">
        <div className="mb-8">
          <Button variant="ghost" size="sm" onClick={() => navigate('/')}>
            ← 返回首页
          </Button>
          <h1 className="font-[var(--font-heading)] text-xl font-bold mt-3 mb-1">
            {currentDiscussion.topic}
          </h1>
          <p className="text-sm text-[var(--color-studio-fg-muted)]">
            讨论已结束 · {currentDiscussion.panel.length} 位嘉宾 · {utterances.length} 条发言 · {currentDiscussion.currentRound} 轮
          </p>
        </div>

        {/* Panel */}
        <section className="mb-10">
          <h2 className="font-[var(--font-heading)] text-sm font-semibold uppercase tracking-wider text-[var(--color-studio-fg-muted)] mb-4">
            👥 嘉宾阵容
          </h2>
          <div className="flex flex-wrap gap-3">
            {currentDiscussion.panel.map((m) => (
              <div
                key={m.id}
                className="flex items-center gap-2.5 px-3 py-2 bg-[var(--color-studio-card)] border border-[var(--color-studio-border-light)] rounded-[var(--radius-sm)]"
              >
                <div
                  className="w-6 h-6 rounded-full flex items-center justify-center font-[var(--font-heading)] font-bold text-[10px] text-white"
                  style={{ backgroundColor: m.color }}
                >
                  {m.name.charAt(0)}
                </div>
                <span className="text-sm font-medium" style={{ color: m.color }}>
                  {m.role === 'host' ? '🎤 ' : ''}{m.name}
                </span>
                <span className="text-[11px] text-[var(--color-studio-fg-dim)]">{m.title}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Consensus & Disagreement */}
        <section className="mb-10">
          <h2 className="font-[var(--font-heading)] text-sm font-semibold uppercase tracking-wider text-[var(--color-studio-fg-muted)] mb-4">
            📋 共识与分歧 ({allConsensus.length})
          </h2>
          {allConsensus.length > 0 ? (
            <ConsensusPanel items={allConsensus} />
          ) : (
            <EmptyState icon="📋" title="本次讨论未产生共识或分歧记录" />
          )}
        </section>

        {/* Transcript */}
        <section className="mb-10">
          <h2 className="font-[var(--font-heading)] text-sm font-semibold uppercase tracking-wider text-[var(--color-studio-fg-muted)] mb-4">
            💬 完整讨论记录
          </h2>
          <div className="bg-[var(--color-studio-card)] border border-[var(--color-studio-border-light)] rounded-[var(--radius-md)] overflow-hidden">
            {utterances.length > 0 ? (
              utterances.map((u) => (
                <div key={u.id} className="border-b border-[var(--color-studio-border-light)] last:border-b-0">
                  <div className="flex items-start gap-3 p-4">
                    <div className="w-[3px] h-full rounded-[2px] flex-shrink-0" style={{ backgroundColor: u.memberColor }} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-sm" style={{ color: u.memberColor }}>{u.memberName}</span>
                        <span className="text-[11px] text-[var(--color-studio-fg-dim)]">{u.memberTitle}</span>
                      </div>
                      <p className="text-sm leading-relaxed">{u.content}</p>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <EmptyState icon="💬" title="暂无发言记录" />
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
