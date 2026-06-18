import { useEffect, useRef, useCallback, useState } from 'react';
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
import {
  startDiscussion,
  pauseDiscussion,
  resumeDiscussion,
  advanceDiscussion,
  endDiscussion,
  fetchDiscussionDetail,
} from '../api/discussions';
import type { WsServerEvent } from '../types/ws';

export function StudioPage() {
  const { discussionId } = useParams<{ discussionId: string }>();
  const navigate = useNavigate();
  const { fetchDetail, detailLoading, detailError, currentDiscussion } = useDiscussionStore();
  const addToast = useToastStore((s) => s.addToast);
  const wsRef = useRef<StudioWebSocket | null>(null);
  const [starting, setStarting] = useState(false);
  const initRef = useRef(false); // 防止重复初始化

  // ── Init: fetch detail ──
  useEffect(() => {
    if (!discussionId) return;
    initRef.current = false;
    useDiscussionStore.getState().clearCurrent();
    useStudioStore.getState().reset();
    fetchDetail(discussionId);
    return () => {
      wsRef.current?.close();
      useStudioStore.getState().reset();
    };
  }, [discussionId]);

  // ── When detail loads, init store ──
  useEffect(() => {
    if (!currentDiscussion || !discussionId) return;
    if (initRef.current) return;
    if (currentDiscussion.status === 'ended') {
      navigate(`/report/${discussionId}`, { replace: true });
      return;
    }

    const isCreator = currentDiscussion.creatorSessionId === getSessionId();
    try {
      useStudioStore.getState().init(currentDiscussion, isCreator);
      initRef.current = true;
    } catch {
      addToast({ type: 'error', message: '初始化讨论失败' });
    }
  }, [currentDiscussion, discussionId]);

  // ── WebSocket 连接 (live/paused 状态时) ──
  useEffect(() => {
    if (!discussionId || !currentDiscussion) return;
    const s = useStudioStore.getState();
    if (currentDiscussion.status !== 'live' && currentDiscussion.status !== 'paused') return;
    if (s.wsStatus === 'connected') return;

    const eventHandler = (event: WsServerEvent) => {
      const st = useStudioStore.getState();
      switch (event.type) {
        case 'expert_status': st.handleExpertStatus(event.data); break;
        case 'utterance_token': st.handleUtteranceToken(event.data); break;
        case 'utterance_complete': st.handleUtteranceComplete({
          id: event.data.utteranceId, panelMemberId: event.data.memberId,
          memberName: event.data.memberName, memberTitle: event.data.memberTitle,
          memberColor: event.data.memberColor, content: event.data.content,
          utteranceType: event.data.utteranceType, sequenceNum: event.data.sequenceNum,
          roundNum: event.data.roundNum, createdAt: event.data.createdAt,
        }); break;
        case 'consensus_update': st.handleConsensusUpdate(event.data); break;
        case 'discussion_paused': st.handleDiscussionPaused(); addToast({ type: 'info', message: '讨论已暂停' }); break;
        case 'discussion_resumed': st.handleDiscussionResumed(); addToast({ type: 'info', message: '讨论已继续' }); break;
        case 'discussion_ended': st.handleDiscussionEnded(); addToast({ type: 'info', message: '讨论已结束' }); break;
        case 'discussion_control': addToast({ type: 'info', message: event.data.message }); break;
        case 'initial_snapshot': st.handleInitialSnapshot(event.data); break;
      }
    };

    useStudioStore.getState().setWsStatus('connecting');
    const ws = new StudioWebSocket(discussionId, getSessionId(), eventHandler);
    wsRef.current = ws;
    ws.connect();

    const timer = setTimeout(() => {
      if (wsRef.current === ws) useStudioStore.getState().setWsStatus('connected');
    }, 2000);

    return () => { clearTimeout(timer); ws.close(); };
  }, [discussionId, currentDiscussion?.status]);

  // ── REST polling fallback (live/paused 时轮询) ──
  useEffect(() => {
    if (!discussionId) return;
    if (currentDiscussion?.status !== 'live' && currentDiscussion?.status !== 'paused') return;

    const interval = setInterval(async () => {
      try {
        const res = await fetchDiscussionDetail(discussionId);
        const detail = res.data;
        if (detail.transcript && detail.transcript.length > 0) {
          const s = useStudioStore.getState();
          const existingIds = new Set(s.utterances.map((u) => u.id));
          const newUtterances = detail.transcript.filter(
            (u: any) => !existingIds.has(u.id),
          );
          if (newUtterances.length > 0) {
            s.handleInitialSnapshot({
              transcript: [
                ...s.utterances,
                ...newUtterances.map((u: any) => ({
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
                })),
              ],
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
  }, [discussionId, currentDiscussion?.status]);

  // ── 点击「开始讨论」— 直接在 pending 视图中处理 ──
  const handleStart = async () => {
    if (!discussionId) return;
    setStarting(true);
    try {
      await startDiscussion(discussionId);
      // 更新 currentDiscussion.status → 触发 WS useEffect + 演播厅视图
      useDiscussionStore.setState((s) => ({
        currentDiscussion: s.currentDiscussion
          ? { ...s.currentDiscussion, status: 'live' as const }
          : null,
      }));
      addToast({ type: 'success', message: '讨论已开始' });
    } catch (e: any) {
      addToast({ type: 'error', message: e.message || '开始讨论失败' });
    } finally {
      setStarting(false);
    }
  };

  // ── Control commands ──
  const sendCommand = useCallback(
    async (type: 'advance' | 'pause' | 'resume' | 'end') => {
      if (!discussionId) return;
      const s = useStudioStore.getState();
      try {
        if (type === 'pause') {
          await pauseDiscussion(discussionId);
          s.handleDiscussionPaused();
          addToast({ type: 'info', message: '讨论已暂停' });
        } else if (type === 'resume') {
          await resumeDiscussion(discussionId);
          s.handleDiscussionResumed();
          addToast({ type: 'info', message: '讨论已继续' });
        } else if (type === 'advance') {
          await advanceDiscussion(discussionId);
          addToast({ type: 'info', message: '已触发下一轮发言' });
        } else if (type === 'end') {
          await endDiscussion(discussionId);
          s.handleDiscussionEnded();
          addToast({ type: 'info', message: '讨论已结束' });
        }
      } catch (e: any) {
        addToast({ type: 'error', message: e.message || '操作失败，请重试' });
      }
    },
    [discussionId, addToast],
  );

  // ── Selectors ──
  const status = useStudioStore((s) => s.status);
  const currentRound = useStudioStore((s) => s.currentRound);
  const maxRounds = useStudioStore((s) => s.maxRounds);
  const totalUtterances = useStudioStore((s) => s.totalUtterances);
  const isCreator = useStudioStore((s) => s.isCreator);
  const members = useStudioStore((s) => s.members);
  const utterances = useStudioStore((s) => s.utterances);
  const streaming = useStudioStore((s) => s.streaming);
  const consensusItems = useStudioStore((s) => s.consensusItems);
  const disagreementItems = useStudioStore((s) => s.disagreementItems);
  const expertStatuses = useStudioStore((s) => s.expertStatuses);
  const wsStatus = useStudioStore((s) => s.wsStatus);

  const allConsensus = [
    ...consensusItems.map((c) => ({ ...c, type: 'consensus' as const })),
    ...disagreementItems.map((d) => ({ ...d, type: 'disagreement' as const })),
  ];

  // ── Loading / Error ──
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

  // ── Pending: 显示嘉宾预览 + 开始按钮 ──
  if (currentDiscussion.status === 'pending') {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-6 px-4">
        <div className="text-center">
          <h2 className="text-xl font-bold text-[var(--color-studio-fg)] mb-2">
            「{currentDiscussion.topic}」
          </h2>
          <p className="text-sm text-[var(--color-studio-fg-muted)] mb-1">
            嘉宾阵容已就绪，共 {currentDiscussion.panel.length} 位嘉宾
          </p>
          <p className="text-xs text-[var(--color-studio-fg-subtle)]">
            点击下方按钮开始圆桌讨论
          </p>
        </div>

        {/* 嘉宾预览 */}
        <div className="flex flex-wrap gap-3 justify-center max-w-lg">
          {currentDiscussion.panel.map((m) => (
            <div key={m.id} className="flex items-center gap-2 px-3 py-2 rounded-lg
              bg-[var(--color-studio-card)] border border-[var(--color-studio-border)]">
              <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: m.color }} />
              <div className="text-left">
                <div className="text-xs text-[var(--color-studio-fg)] font-medium">{m.name}</div>
                <div className="text-[10px] text-[var(--color-studio-fg-muted)]">
                  {m.role === 'host' ? '主持人' : '嘉宾'} · {m.title}
                </div>
              </div>
            </div>
          ))}
        </div>

        {isCreator ? (
          <Button variant="primary" size="lg" loading={starting} onClick={handleStart}>
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8 5v14l11-7z" />
            </svg>
            开始讨论
          </Button>
        ) : (
          <p className="text-sm text-[var(--color-studio-fg-muted)]">等待主持人开始讨论…</p>
        )}
      </div>
    );
  }

  // ── 演播厅视图 (live / paused) ──
  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* topic bar */}
      <div className="flex items-center justify-center py-1.5 px-4
        bg-[var(--color-studio-elevated)] border-b border-[var(--color-studio-border)] shrink-0">
        <span className="text-sm text-[var(--color-studio-fg-muted)] truncate">
          「{currentDiscussion.topic}」— 第 {currentRound} 轮
        </span>
        {wsStatus !== 'connected' && (
          <span className="ml-3 text-[11px] text-[var(--color-studio-warning)]">
            {wsStatus === 'connecting' ? '连接中…' : wsStatus === 'reconnecting' ? '重连中…' : '已断开'}
          </span>
        )}
      </div>

      {/* Expert strip (小屏水平滚动) */}
      <div className="flex lg:hidden gap-2 px-4 py-2
        bg-[var(--color-studio-elevated)] border-b border-[var(--color-studio-border)] overflow-x-auto shrink-0">
        <ExpertStatusPanel members={members} statuses={expertStatuses} compact />
      </div>

      {/* Studio Grid — responsive */}
      <div className="flex-1 overflow-hidden grid grid-cols-1 md:grid-cols-[1fr_280px] lg:grid-cols-[280px_1fr_320px]">
        {/* Left: Expert Panel */}
        <aside className="hidden lg:flex flex-col overflow-y-auto border-r border-[var(--color-studio-border)]">
          <div className="sticky top-0 z-[var(--z-sticky)] flex items-center gap-2 px-4 py-3
            bg-[var(--color-studio-elevated)] border-b border-[var(--color-studio-border)]
            font-semibold text-xs uppercase tracking-wider">
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
          <div className="sticky top-0 z-[var(--z-sticky)] flex items-center gap-2 px-4 py-3
            bg-[var(--color-studio-elevated)] border-b border-[var(--color-studio-border)]
            font-semibold text-xs uppercase tracking-wider">
            <svg className="w-4 h-4 opacity-70" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
            </svg>
            讨论记录
          </div>
          <TranscriptView utterances={utterances} streaming={streaming} />
        </section>

        {/* Right: Consensus */}
        <aside className="flex flex-col overflow-y-auto">
          <div className="sticky top-0 z-[var(--z-sticky)] flex items-center gap-2 px-4 py-3
            bg-[var(--color-studio-elevated)] border-b border-[var(--color-studio-border)]
            font-semibold text-xs uppercase tracking-wider">
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
          <Button variant="primary" onClick={() => navigate(`/report/${discussionId}`)}>
            查看讨论报告 →
          </Button>
        </div>
      )}
    </div>
  );
}
