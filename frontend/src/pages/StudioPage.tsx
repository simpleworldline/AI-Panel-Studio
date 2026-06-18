import { useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDiscussionStore } from '../store/useDiscussionStore';
import { useStudioStore } from '../store/useStudioStore';
import { useToastStore } from '../store/useToastStore';
import { getSessionId } from '../utils/session';
import { StudioWebSocket } from '../ws/wsClient';
import { ExpertStatusPanel } from '../components/ExpertStatusPanel';
import { TranscriptView } from '../components/TranscriptView';
import { ConsensusPanel } from '../components/ConsensusPanel';
import { ControlBar } from '../components/ControlBar';
import { Spinner } from '../components/ui/Spinner';
import { Button } from '../components/ui/Button';
import { pauseDiscussion, resumeDiscussion, advanceDiscussion, endDiscussion, fetchDiscussionDetail } from '../api/discussions';
import type { WsServerEvent } from '../types/ws';

export function StudioPage() {
  const { discussionId } = useParams<{ discussionId: string }>();
  const navigate = useNavigate();
  const { fetchDetail, detailLoading, detailError, currentDiscussion } = useDiscussionStore();
  const addToast = useToastStore((s) => s.addToast);
  const wsRef = useRef<StudioWebSocket | null>(null);

  // Initialize
  useEffect(() => {
    if (!discussionId) return;
    // 先清空上次讨论数据，避免跨页面污染导致闪白
    useDiscussionStore.getState().clearCurrent();
    useStudioStore.getState().reset();
    fetchDetail(discussionId);
    return () => {
      wsRef.current?.close();
      useStudioStore.getState().reset();
    };
  }, [discussionId]);

  // When detail loads, init store and connect WS
  useEffect(() => {
    if (!currentDiscussion || !discussionId) return;

    // If discussion is ended, redirect to report
    if (currentDiscussion.status === 'ended') {
      navigate(`/report/${discussionId}`, { replace: true });
      return;
    }

    const isCreator = currentDiscussion.creatorSessionId === getSessionId();
    try {
      useStudioStore.getState().init(currentDiscussion, isCreator);
    } catch (err) {
      console.error('StudioPage init failed:', err);
      addToast({ type: 'error', message: '初始化讨论失败' });
      return;
    }

    // Connect WebSocket
    const eventHandler = (event: WsServerEvent) => {
      const s = useStudioStore.getState();
      switch (event.type) {
        case 'expert_status':
          s.handleExpertStatus(event.data);
          break;
        case 'utterance_token':
          s.handleUtteranceToken(event.data);
          break;
        case 'utterance_complete':
          s.handleUtteranceComplete({
            id: event.data.utteranceId,
            panelMemberId: event.data.memberId,
            memberName: event.data.memberName,
            memberTitle: event.data.memberTitle,
            memberColor: event.data.memberColor,
            content: event.data.content,
            utteranceType: event.data.utteranceType,
            sequenceNum: event.data.sequenceNum,
            roundNum: event.data.roundNum,
            createdAt: event.data.createdAt,
          });
          break;
        case 'consensus_update':
          s.handleConsensusUpdate(event.data);
          break;
        case 'discussion_paused':
          s.handleDiscussionPaused();
          addToast({ type: 'info', message: '讨论已暂停' });
          break;
        case 'discussion_resumed':
          s.handleDiscussionResumed();
          addToast({ type: 'info', message: '讨论已继续' });
          break;
        case 'discussion_ended':
          s.handleDiscussionEnded();
          addToast({ type: 'info', message: '讨论已结束' });
          break;
        case 'discussion_control':
          addToast({ type: 'info', message: event.data.message });
          break;
        case 'initial_snapshot':
          s.handleInitialSnapshot(event.data);
          break;
      }
    };

    useStudioStore.getState().setWsStatus('connecting');
    const ws = new StudioWebSocket(discussionId, getSessionId(), eventHandler);
    wsRef.current = ws;
    ws.connect();

    // Check connection after 2s
    const checkTimer = setTimeout(() => {
      if (wsRef.current === ws) {
        useStudioStore.getState().setWsStatus('connected');
      }
    }, 2000);

    return () => {
      clearTimeout(checkTimer);
      ws.close();
    };
  }, [currentDiscussion, discussionId]);

  // ── REST 轮询兜底：每 3s 同步一次 transcript，确保 WS 断开时数据不丢失 ──
  useEffect(() => {
    if (!discussionId) return;
    const interval = setInterval(async () => {
      try {
        const res = await fetchDiscussionDetail(discussionId);
        const detail = res.data;
        if (detail.transcript && detail.transcript.length > 0) {
          const s = useStudioStore.getState();
          const existingIds = new Set(s.utterances.map(u => u.id));
          const newUtterances = detail.transcript.filter(
            (u: any) => !existingIds.has(u.id)
          );
          if (newUtterances.length > 0) {
            s.handleInitialSnapshot({
              transcript: [...s.utterances, ...newUtterances.map((u: any) => ({
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
              }))],
              currentRound: detail.currentRound,
              totalUtterances: detail.transcript.length,
            });
          }
        }
      } catch {
        // ignore polling errors
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [discussionId]);
  const sendCommand = useCallback(
    async (type: 'advance' | 'pause' | 'resume' | 'end') => {
      if (!discussionId) return;
      try {
        if (type === 'pause') {
          await pauseDiscussion(discussionId);
          addToast({ type: 'info', message: '讨论已暂停' });
        } else if (type === 'resume') {
          await resumeDiscussion(discussionId);
          addToast({ type: 'info', message: '讨论已继续' });
        } else if (type === 'advance') {
          await advanceDiscussion(discussionId);
        } else if (type === 'end') {
          await endDiscussion(discussionId);
          addToast({ type: 'info', message: '讨论已结束' });
        }
      } catch {
        addToast({ type: 'error', message: '操作失败，请重试' });
      }
    },
    [discussionId, addToast],
  );

  // Loading state
  if (detailLoading || !currentDiscussion) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  // Error state
  if (detailError) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <p className="text-[var(--color-studio-destructive)] mb-4">{detailError}</p>
          <Button variant="primary" onClick={() => navigate('/')}>返回首页</Button>
        </div>
      </div>
    );
  }

  // 使用选择器 —— Zustand v4 必须精确订阅才能触发重渲染
  const status = useStudioStore(s => s.status);
  const currentRound = useStudioStore(s => s.currentRound);
  const maxRounds = useStudioStore(s => s.maxRounds);
  const totalUtterances = useStudioStore(s => s.totalUtterances);
  const isCreator = useStudioStore(s => s.isCreator);
  const members = useStudioStore(s => s.members);
  const utterances = useStudioStore(s => s.utterances);
  const streaming = useStudioStore(s => s.streaming);
  const consensusItems = useStudioStore(s => s.consensusItems);
  const disagreementItems = useStudioStore(s => s.disagreementItems);
  const expertStatuses = useStudioStore(s => s.expertStatuses);
  const wsStatus = useStudioStore(s => s.wsStatus);

  // Build combined consensus list (both consensus and disagreement)
  const allConsensus = [
    ...consensusItems.map((c) => ({ ...c, type: 'consensus' as const })),
    ...disagreementItems.map((d) => ({ ...d, type: 'disagreement' as const })),
  ];

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Topic bar */}
      <div className="flex items-center justify-center py-1.5 px-4 bg-[var(--color-studio-elevated)] border-b border-[var(--color-studio-border)] flex-shrink-0">
        <span className="text-sm text-[var(--color-studio-fg-muted)] truncate">
          「{currentDiscussion.topic}」— 第 {currentRound} 轮进行中
        </span>
        {wsStatus !== 'connected' && (
          <span className="ml-3 text-[11px] text-[var(--color-studio-warning)]">
            {wsStatus === 'connecting' ? '连接中...' : wsStatus === 'reconnecting' ? '重连中...' : '已断开'}
          </span>
        )}
      </div>

      {/* Expert Strip (visible 800-1399px) */}
      <div className="hidden md:flex lg:hidden gap-2 px-4 py-2 bg-[var(--color-studio-elevated)] border-b border-[var(--color-studio-border)] overflow-x-auto flex-shrink-0">
        <ExpertStatusPanel members={members} statuses={expertStatuses} compact />
      </div>

      {/* Studio Grid */}
      <div
        className="flex-1 overflow-hidden"
        style={{
          display: 'grid',
          gridTemplateColumns: '280px 1fr 320px',
        }}
      >
        {/* Left: Expert Panel (hidden < 1400px via responsive class) */}
        <aside className="hidden lg:flex flex-col overflow-y-auto border-r border-[var(--color-studio-border)]">
          <div className="sticky top-0 z-[var(--z-sticky)] flex items-center gap-2 px-4 py-3.5 bg-[var(--color-studio-elevated)] border-b border-[var(--color-studio-border)] font-[var(--font-heading)] text-xs font-semibold uppercase tracking-wider">
            <svg className="w-4 h-4 opacity-70" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="8" r="4" />
              <path d="M6 21v-2a4 4 0 014-4h4a4 4 0 014 4v2" />
            </svg>
            嘉宾状态
          </div>
          <div className="p-3">
            <ExpertStatusPanel members={members} statuses={expertStatuses} />
          </div>
        </aside>

        {/* Center: Transcript */}
        <section className="flex flex-col overflow-hidden border-r border-[var(--color-studio-border)]">
          <div className="sticky top-0 z-[var(--z-sticky)] flex items-center gap-2 px-4 py-3.5 bg-[var(--color-studio-elevated)] border-b border-[var(--color-studio-border)] font-[var(--font-heading)] text-xs font-semibold uppercase tracking-wider">
            <svg className="w-4 h-4 opacity-70" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
            </svg>
            讨论记录
          </div>
          <TranscriptView utterances={utterances} streaming={streaming} />
        </section>

        {/* Right: Consensus */}
        <aside className="flex flex-col overflow-y-auto">
          <div className="sticky top-0 z-[var(--z-sticky)] flex items-center gap-2 px-4 py-3.5 bg-[var(--color-studio-elevated)] border-b border-[var(--color-studio-border)] font-[var(--font-heading)] text-xs font-semibold uppercase tracking-wider">
            <svg className="w-4 h-4 opacity-70" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2" />
              <rect x="9" y="3" width="6" height="4" rx="1" />
            </svg>
            共识与分歧
          </div>
          <div className="p-3">
            <ConsensusPanel items={allConsensus} />
          </div>
        </aside>
      </div>

      {/* Control Bar */}
      <ControlBar
        status={status}
        currentRound={currentRound}
        totalUtterances={totalUtterances}
        maxRounds={maxRounds}
        isCreator={isCreator}
        onPause={() => sendCommand('pause')}
        onResume={() => sendCommand('resume')}
        onAdvance={() => sendCommand('advance')}
        onEnd={() => sendCommand('end')}
      />

      {status === 'ended' && (
        <div className="absolute bottom-16 left-1/2 -translate-x-1/2">
          <Button
            variant="primary"
            onClick={() => navigate(`/report/${discussionId}`)}
          >
            查看讨论报告 →
          </Button>
        </div>
      )}
    </div>
  );
}
