import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useToastStore } from '../store/useToastStore';
import { usePanelStore } from '../store/usePanelStore';
import { useStudioStore } from '../store/useStudioStore';
import { useDiscussionStore } from '../store/useDiscussionStore';

// ============================================================
// Toast Store
// ============================================================
describe('useToastStore', () => {
  beforeEach(() => {
    useToastStore.setState({ toasts: [] });
  });

  it('addToast: 添加通知，自动分配 ID', () => {
    useToastStore.getState().addToast({ type: 'success', message: '成功' });
    const toasts = useToastStore.getState().toasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].type).toBe('success');
    expect(toasts[0].message).toBe('成功');
    expect(toasts[0].id).toBeTruthy();
  });

  it('addToast: 多次添加', () => {
    useToastStore.getState().addToast({ type: 'info', message: 'a' });
    useToastStore.getState().addToast({ type: 'error', message: 'b' });
    expect(useToastStore.getState().toasts).toHaveLength(2);
  });

  it('removeToast: 移除指定通知', () => {
    useToastStore.getState().addToast({ type: 'info', message: 'a' });
    const id = useToastStore.getState().toasts[0].id;
    useToastStore.getState().removeToast(id);
    expect(useToastStore.getState().toasts).toHaveLength(0);
  });
});

// ============================================================
// Panel Store
// ============================================================
describe('usePanelStore', () => {
  beforeEach(() => {
    usePanelStore.getState().reset();
  });

  it('init: 正确设置 discussionId 和 expertCount', () => {
    usePanelStore.getState().init('disc-1', 6);
    const s = usePanelStore.getState();
    expect(s.discussionId).toBe('disc-1');
    expect(s.expertCount).toBe(6);
    expect(s.host).toBeNull();
    expect(s.experts).toEqual([]);
  });

  it('generate: 填充 host 和 experts', async () => {
    const mockApi = await import('../api/panel');
    vi.spyOn(mockApi, 'generatePanel').mockResolvedValueOnce({
      code: 200,
      data: {
        host: { name: '张明', title: 'AI伦理学家', stance: '中立', color: '#6366F1' },
        experts: [
          { name: '李四', title: '研究员', stance: '支持', color: '#EF4444' },
          { name: '王五', title: '教授', stance: '反对', color: '#10B981' },
        ],
      },
      message: 'success',
    });

    usePanelStore.getState().init('disc-1', 2);
    await usePanelStore.getState().generate('disc-1');

    const s = usePanelStore.getState();
    expect(s.host).toBeTruthy();
    expect(s.host?.name).toBe('张明');
    expect(s.experts).toHaveLength(2);
    expect(s.generating).toBe(false);
    expect(s.generateError).toBeNull();
  });

  it('generate: 失败时设置错误', async () => {
    const mockApi = await import('../api/panel');
    vi.spyOn(mockApi, 'generatePanel').mockRejectedValueOnce({ message: '生成失败' });

    usePanelStore.getState().init('disc-1', 2);
    await usePanelStore.getState().generate('disc-1');

    expect(usePanelStore.getState().generateError).toBe('生成失败');
    expect(usePanelStore.getState().generating).toBe(false);
  });

  it('updateHost: 更新主持人字段', () => {
    usePanelStore.setState({
      host: { name: '原', title: 'T', stance: 'S', color: '#000000' },
    });
    usePanelStore.getState().updateHost({ name: '新名字' });
    expect(usePanelStore.getState().host?.name).toBe('新名字');
    expect(usePanelStore.getState().host?.title).toBe('T'); // 未改字段保持
  });

  it('updateExpert: 更新指定嘉宾', () => {
    usePanelStore.setState({
      experts: [
        { name: 'A', title: 'TA', stance: 'SA', color: '#111111' },
        { name: 'B', title: 'TB', stance: 'SB', color: '#222222' },
      ],
    });
    usePanelStore.getState().updateExpert(1, { name: 'B-new', color: '#333333' });
    const experts = usePanelStore.getState().experts;
    expect(experts[0].name).toBe('A'); // 不变
    expect(experts[1].name).toBe('B-new');
    expect(experts[1].color).toBe('#333333');
  });

  it('reset: 恢复为空状态', () => {
    usePanelStore.getState().init('disc-1', 4);
    usePanelStore.setState({ host: { name: 'X', title: 'Y', stance: 'Z', color: '#000' } });
    usePanelStore.getState().reset();
    const s = usePanelStore.getState();
    expect(s.discussionId).toBe('');
    expect(s.host).toBeNull();
    expect(s.experts).toEqual([]);
  });
});

// ============================================================
// Studio Store
// ============================================================
describe('useStudioStore', () => {
  beforeEach(() => {
    useStudioStore.getState().reset();
  });

  it('init: 从 DiscussionDetail 初始化', () => {
    const detail = {
      id: 'd-1',
      topic: '测试话题',
      expertCount: 3,
      status: 'live' as const,
      currentRound: 0,
      maxRounds: null,
      createdAt: '2026-06-17T10:00:00Z',
      endedAt: null,
      creatorSessionId: 'sid-1',
      panel: [
        { id: 'pm-1', name: '主持人', title: 'T', role: 'host' as const, stance: '中立', color: '#6366F1' },
        { id: 'pm-2', name: '专家A', title: 'TA', role: 'expert' as const, stance: '支持', color: '#EF4444' },
      ],
      transcript: [],
      consensus: [],
      disagreements: [],
    };

    useStudioStore.getState().init(detail, true);

    const s = useStudioStore.getState();
    expect(s.discussionId).toBe('d-1');
    expect(s.topic).toBe('测试话题');
    expect(s.status).toBe('live');
    expect(s.isCreator).toBe(true);
    expect(s.members).toHaveLength(2);
    expect(s.utterances).toEqual([]);
  });

  it('handleExpertStatus: 新增/更新专家状态', () => {
    useStudioStore.getState().handleExpertStatus({
      memberId: 'pm-2',
      memberName: '专家A',
      memberColor: '#EF4444',
      status: 'preparing',
      focusSummary: '正在思考 AI 边界',
      desireValue: 0.85,
      timestamp: '2026-06-17T10:05:00Z',
    });

    const statuses = useStudioStore.getState().expertStatuses;
    expect(statuses['pm-2']).toBeTruthy();
    expect(statuses['pm-2'].status).toBe('preparing');
    expect(statuses['pm-2'].desireValue).toBe(0.85);
  });

  it('handleUtteranceToken: 首次 token 创建 streaming', () => {
    useStudioStore.getState().handleUtteranceToken({
      utteranceId: 'u-1',
      memberId: 'pm-2',
      memberName: '专家A',
      memberTitle: '研究员',
      memberColor: '#EF4444',
      token: '我认',
      isFirst: true,
      isLast: false,
    });

    const s = useStudioStore.getState().streaming;
    expect(s).toBeTruthy();
    expect(s?.utteranceId).toBe('u-1');
    expect(s?.accumulatedText).toBe('我认');
    expect(s?.isStreaming).toBe(true);
  });

  it('handleUtteranceToken: 追加 token', () => {
    // first
    useStudioStore.getState().handleUtteranceToken({
      utteranceId: 'u-1', memberId: 'pm-2', memberName: '专家A',
      memberTitle: '研究员', memberColor: '#EF4444',
      token: '我认', isFirst: true, isLast: false,
    });
    // second
    useStudioStore.getState().handleUtteranceToken({
      utteranceId: 'u-1', memberId: 'pm-2', memberName: '专家A',
      memberTitle: '研究员', memberColor: '#EF4444',
      token: '为', isFirst: false, isLast: false,
    });
    // third (last)
    useStudioStore.getState().handleUtteranceToken({
      utteranceId: 'u-1', memberId: 'pm-2', memberName: '专家A',
      memberTitle: '研究员', memberColor: '#EF4444',
      token: '…', isFirst: false, isLast: true,
    });

    expect(useStudioStore.getState().streaming?.accumulatedText).toBe('我认为…');
    expect(useStudioStore.getState().streaming?.isStreaming).toBe(false);
  });

  it('handleUtteranceComplete: 写入 utterances，清除 streaming', () => {
    // 先模拟有 streaming
    useStudioStore.setState({
      streaming: {
        utteranceId: 'u-1', memberId: 'pm-2', memberName: '专家A',
        memberTitle: '研究员', memberColor: '#EF4444',
        accumulatedText: '完整发言', isStreaming: true,
      },
    });

    useStudioStore.getState().handleUtteranceComplete({
      id: 'u-1',
      panelMemberId: 'pm-2',
      memberName: '专家A',
      memberTitle: '研究员',
      memberColor: '#EF4444',
      content: '完整发言',
      utteranceType: 'statement',
      sequenceNum: 1,
      roundNum: 1,
      createdAt: '2026-06-17T10:01:00Z',
    });

    const s = useStudioStore.getState();
    expect(s.utterances).toHaveLength(1);
    expect(s.utterances[0].content).toBe('完整发言');
    expect(s.streaming).toBeNull();
    expect(s.currentRound).toBe(1);
  });

  it('handleConsensusUpdate: created — 共识', () => {
    useStudioStore.getState().handleConsensusUpdate({
      action: 'created',
      record: {
        id: 'c-1', type: 'consensus', title: '达成共识',
        description: '双方认同', sourceUtteranceIds: ['u-1', 'u-2'],
        confidence: 0.92, isResolved: false, roundNum: 2,
      },
    });
    expect(useStudioStore.getState().consensusItems).toHaveLength(1);
  });

  it('handleConsensusUpdate: created — 分歧', () => {
    useStudioStore.getState().handleConsensusUpdate({
      action: 'created',
      record: {
        id: 'd-1', type: 'disagreement', title: '观点分歧',
        description: '无法调和', sourceUtteranceIds: ['u-3'],
        confidence: 0.75, isResolved: false, roundNum: 2,
      },
    });
    expect(useStudioStore.getState().disagreementItems).toHaveLength(1);
  });

  it('handleConsensusUpdate: updated — 更新已有记录', () => {
    useStudioStore.setState({
      consensusItems: [{
        id: 'c-1', type: 'consensus', title: '旧标题',
        description: '旧描述', sourceUtteranceIds: ['u-1'],
        confidence: 0.5, isResolved: false, roundNum: 1,
      }],
    });
    useStudioStore.getState().handleConsensusUpdate({
      action: 'updated',
      record: {
        id: 'c-1', type: 'consensus', title: '新标题',
        description: '新描述', sourceUtteranceIds: ['u-1', 'u-2'],
        confidence: 0.9, isResolved: false, roundNum: 2,
      },
    });
    expect(useStudioStore.getState().consensusItems[0].title).toBe('新标题');
    expect(useStudioStore.getState().consensusItems[0].confidence).toBe(0.9);
  });

  it('handleConsensusUpdate: resolved — 标记为已化解', () => {
    useStudioStore.setState({
      disagreementItems: [{
        id: 'd-1', type: 'disagreement', title: '分歧',
        description: '...', sourceUtteranceIds: ['u-1'],
        confidence: 0.7, isResolved: false, roundNum: 1,
      }],
    });
    useStudioStore.getState().handleConsensusUpdate({
      action: 'resolved',
      record: { id: 'd-1', type: 'disagreement', title: '分歧', description: '...', sourceUtteranceIds: ['u-1'], confidence: 0.7, isResolved: true, roundNum: 1 },
    });
    expect(useStudioStore.getState().disagreementItems[0].isResolved).toBe(true);
  });

  it('handleDiscussionPaused / handleDiscussionResumed: 状态切换', () => {
    useStudioStore.getState().handleDiscussionPaused();
    expect(useStudioStore.getState().status).toBe('paused');

    useStudioStore.getState().handleDiscussionResumed();
    expect(useStudioStore.getState().status).toBe('live');
  });

  it('handleDiscussionEnded: 标记结束 + 停止 streaming', () => {
    useStudioStore.setState({
      streaming: {
        utteranceId: 'u-1', memberId: 'p-1', memberName: 'A',
        memberTitle: 'T', memberColor: '#000',
        accumulatedText: 'text', isStreaming: true,
      },
    });
    useStudioStore.getState().handleDiscussionEnded();
    expect(useStudioStore.getState().status).toBe('ended');
    expect(useStudioStore.getState().streaming?.isStreaming).toBe(false);
  });

  it('setWsStatus: 更新 WebSocket 连接状态', () => {
    useStudioStore.getState().setWsStatus('connected');
    expect(useStudioStore.getState().wsStatus).toBe('connected');

    useStudioStore.getState().setWsStatus('disconnected');
    expect(useStudioStore.getState().wsStatus).toBe('disconnected');
  });

  it('reset: 恢复初始状态', () => {
    useStudioStore.setState({
      discussionId: 'd-1', topic: 'T', status: 'live', utterances: [{
        id: 'u-1', panelMemberId: '', memberName: '', memberTitle: '',
        memberColor: '', content: '', utteranceType: '', sequenceNum: 0, roundNum: 0, createdAt: '',
      }],
    });
    useStudioStore.getState().reset();
    const s = useStudioStore.getState();
    expect(s.discussionId).toBe('');
    expect(s.topic).toBe('');
    expect(s.utterances).toEqual([]);
    expect(s.wsStatus).toBe('connecting');
  });
});

// ============================================================
// Discussion Store
// ============================================================
describe('useDiscussionStore', () => {
  beforeEach(() => {
    useDiscussionStore.setState({
      discussions: [],
      listLoading: false,
      listError: null,
      currentDiscussion: null,
      detailLoading: false,
      detailError: null,
    });
  });

  it('fetchList: 成功填充列表', async () => {
    const mockApi = await import('../api/discussions');
    vi.spyOn(mockApi, 'fetchDiscussions').mockResolvedValueOnce({
      code: 200,
      data: {
        items: [
          { id: 'd-1', topic: 'Test', expertCount: 4, status: 'live', currentRound: 0, createdAt: '2026', memberPreview: [] },
        ],
        total: 1,
        page: 1,
        pageSize: 20,
      },
      message: 'success',
    });

    await useDiscussionStore.getState().fetchList('live');
    const s = useDiscussionStore.getState();
    expect(s.discussions).toHaveLength(1);
    expect(s.discussions[0].topic).toBe('Test');
    expect(s.listLoading).toBe(false);
    expect(s.listError).toBeNull();
  });

  it('fetchList: 失败设置错误', async () => {
    const mockApi = await import('../api/discussions');
    vi.spyOn(mockApi, 'fetchDiscussions').mockRejectedValueOnce({ message: '网络错误' });

    await useDiscussionStore.getState().fetchList();
    expect(useDiscussionStore.getState().listError).toBe('网络错误');
    expect(useDiscussionStore.getState().listLoading).toBe(false);
  });

  it('clearCurrent: 清除当前详情', () => {
    useDiscussionStore.setState({
      currentDiscussion: { id: 'd-1', topic: 'T' } as any,
      detailLoading: true,
      detailError: 'err',
    });
    useDiscussionStore.getState().clearCurrent();
    const s = useDiscussionStore.getState();
    expect(s.currentDiscussion).toBeNull();
    expect(s.detailLoading).toBe(false);
    expect(s.detailError).toBeNull();
  });

  it('setActiveTab: 切换 Tab', () => {
    useDiscussionStore.getState().setActiveTab('ended');
    expect(useDiscussionStore.getState().activeTab).toBe('ended');
  });
});
