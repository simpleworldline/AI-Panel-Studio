import { create } from 'zustand';
import type { PanelMember, DiscussionDetail } from '../types/discussion';
import type { ConsensusRecord } from '../types/consensus';
import type { ExpertStatus } from '../types/expert';

export interface StreamingUtterance {
  utteranceId: string;
  memberId: string;
  memberName: string;
  memberTitle: string;
  memberColor: string;
  accumulatedText: string;
  isStreaming: boolean;
}

export interface UtteranceDisplay {
  id: string;
  panelMemberId: string;
  memberName: string;
  memberTitle: string;
  memberColor: string;
  content: string;
  utteranceType: string;
  sequenceNum: number;
  roundNum: number;
  createdAt: string;
}

interface StudioStoreState {
  discussionId: string;
  topic: string;
  status: 'live' | 'paused' | 'ended';
  isCreator: boolean;
  currentRound: number;
  maxRounds: number | null;
  totalUtterances: number;

  members: PanelMember[];
  utterances: UtteranceDisplay[];
  streaming: StreamingUtterance | null;
  consensusItems: ConsensusRecord[];
  disagreementItems: ConsensusRecord[];
  expertStatuses: Record<string, ExpertStatus>;

  wsStatus: 'connecting' | 'connected' | 'reconnecting' | 'disconnected';

  init: (detail: DiscussionDetail, isCreator: boolean) => void;
  reset: () => void;

  // WS handlers
  handleExpertStatus: (data: {
    memberId: string;
    memberName: string;
    memberColor: string;
    status: ExpertStatus['status'];
    focusSummary: string | null;
    desireValue: number;
    timestamp: string;
  }) => void;
  handleUtteranceToken: (data: {
    utteranceId: string;
    memberId: string;
    memberName: string;
    memberTitle: string;
    memberColor: string;
    token: string;
    isFirst: boolean;
    isLast: boolean;
  }) => void;
  handleUtteranceComplete: (data: UtteranceDisplay & { utteranceType: string }) => void;
  handleConsensusUpdate: (data: {
    action: 'created' | 'updated' | 'resolved';
    record: ConsensusRecord;
  }) => void;
  handleDiscussionPaused: () => void;
  handleDiscussionResumed: () => void;
  handleDiscussionEnded: () => void;
  setWsStatus: (wsStatus: StudioStoreState['wsStatus']) => void;
}

export const useStudioStore = create<StudioStoreState>((set) => ({
  discussionId: '',
  topic: '',
  status: 'live',
  isCreator: false,
  currentRound: 0,
  maxRounds: null,
  totalUtterances: 0,

  members: [],
  utterances: [],
  streaming: null,
  consensusItems: [],
  disagreementItems: [],
  expertStatuses: {},

  wsStatus: 'connecting',

  init: (detail, isCreator) => {
    set({
      discussionId: detail.id,
      topic: detail.topic,
      status: detail.status === 'ended' ? 'ended' : 'live',
      isCreator,
      currentRound: detail.currentRound,
      maxRounds: detail.maxRounds,
      totalUtterances: detail.transcript.length,
      members: detail.panel,
      utterances: detail.transcript.map((u) => ({
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
      })),
      consensusItems: detail.consensus || [],
      disagreementItems: detail.disagreements || [],
      streaming: null,
    });
  },

  reset: () => {
    set({
      discussionId: '',
      topic: '',
      status: 'live',
      isCreator: false,
      currentRound: 0,
      maxRounds: null,
      totalUtterances: 0,
      members: [],
      utterances: [],
      streaming: null,
      consensusItems: [],
      disagreementItems: [],
      expertStatuses: {},
      wsStatus: 'connecting',
    });
  },

  handleExpertStatus: (data) => {
    set((s) => ({
      expertStatuses: {
        ...s.expertStatuses,
        [data.memberId]: {
          memberId: data.memberId,
          status: data.status,
          focusSummary: data.focusSummary,
          desireValue: data.desireValue,
          timestamp: data.timestamp,
        },
      },
    }));
  },

  handleUtteranceToken: (data) => {
    set((s) => {
      if (!s.streaming || s.streaming.utteranceId !== data.utteranceId) {
        return {
          streaming: {
            utteranceId: data.utteranceId,
            memberId: data.memberId,
            memberName: data.memberName,
            memberTitle: data.memberTitle,
            memberColor: data.memberColor,
            accumulatedText: data.token,
            isStreaming: !data.isLast,
          },
        };
      }
      return {
        streaming: {
          ...s.streaming,
          accumulatedText: s.streaming.accumulatedText + data.token,
          isStreaming: !data.isLast,
        },
      };
    });
  },

  handleUtteranceComplete: (data) => {
    set((s) => ({
      utterances: [
        ...s.utterances,
        {
          id: data.id,
          panelMemberId: data.panelMemberId,
          memberName: data.memberName,
          memberTitle: data.memberTitle,
          memberColor: data.memberColor,
          content: data.content,
          utteranceType: data.utteranceType,
          sequenceNum: data.sequenceNum,
          roundNum: data.roundNum,
          createdAt: data.createdAt,
        },
      ],
      streaming: null,
      currentRound: data.roundNum,
      totalUtterances: data.sequenceNum,
    }));
  },

  handleConsensusUpdate: (data) => {
    set((s) => {
      const isConsensus = data.record.type === 'consensus';
      const key = isConsensus ? 'consensusItems' : 'disagreementItems';
      const list = s[key] as ConsensusRecord[];

      if (data.action === 'created') {
        return { [key]: [...list, data.record] } as any;
      } else if (data.action === 'updated') {
        const idx = list.findIndex((c) => c.id === data.record.id);
        if (idx < 0) return s;
        const updated = [...list];
        updated[idx] = data.record;
        return { [key]: updated } as any;
      } else if (data.action === 'resolved') {
        const idx = list.findIndex((c) => c.id === data.record.id);
        if (idx < 0) return s;
        const updated = [...list];
        updated[idx] = { ...updated[idx], isResolved: true };
        return { [key]: updated } as any;
      }
      return s;
    });
  },

  handleInitialSnapshot: (data: {
    transcript?: UtteranceDisplay[];
    consensus?: any[];
    disagreements?: any[];
    currentRound?: number;
    totalUtterances?: number;
  }) => {
    set((s) => ({
      utterances: data.transcript || s.utterances,
      consensusItems: data.consensus || s.consensusItems,
      disagreementItems: data.disagreements || s.disagreementItems,
      currentRound: data.currentRound ?? s.currentRound,
      totalUtterances: data.totalUtterances ?? s.totalUtterances,
    }));
  },

  handleDiscussionPaused: () => set({ status: 'paused' }),
  handleDiscussionResumed: () => set({ status: 'live' }),
  handleDiscussionEnded: () => {
    set((s) => ({
      status: 'ended' as const,
      streaming: s.streaming ? { ...s.streaming, isStreaming: false } : null,
    }));
  },
  setWsStatus: (wsStatus) => set({ wsStatus }),
}));
