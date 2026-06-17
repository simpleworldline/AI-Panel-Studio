// WebSocket 事件类型 — 与 API_CONTRACT.md §3 对齐

import type { ExpertStatusKind } from './expert';
import type { UtteranceType } from './discussion';
import type { ConsensusType } from './consensus';

// ── S→C 事件 ──

export interface WsExpertStatus {
  type: 'expert_status';
  data: {
    memberId: string;
    memberName: string;
    memberColor: string;
    status: ExpertStatusKind;
    focusSummary: string | null;
    desireValue: number;
    timestamp: string;
  };
}

export interface WsUtteranceToken {
  type: 'utterance_token';
  data: {
    utteranceId: string;
    memberId: string;
    memberName: string;
    memberTitle: string;
    memberColor: string;
    token: string;
    sequenceNum: number;
    roundNum: number;
    isFirst: boolean;
    isLast: boolean;
  };
}

export interface WsUtteranceComplete {
  type: 'utterance_complete';
  data: {
    utteranceId: string;
    memberId: string;
    memberName: string;
    memberTitle: string;
    memberColor: string;
    content: string;
    utteranceType: UtteranceType;
    sequenceNum: number;
    roundNum: number;
    createdAt: string;
  };
}

export interface WsConsensusUpdate {
  type: 'consensus_update';
  data: {
    action: 'created' | 'updated' | 'resolved';
    record: {
      id: string;
      type: ConsensusType;
      title: string;
      description: string;
      sourceUtteranceIds: string[];
      confidence: number;
      isResolved: boolean;
      roundNum: number;
    };
  };
}

export interface WsDiscussionPaused {
  type: 'discussion_paused';
  data: { discussionId: string; timestamp: string };
}

export interface WsDiscussionResumed {
  type: 'discussion_resumed';
  data: { discussionId: string; timestamp: string };
}

export interface WsDiscussionEnded {
  type: 'discussion_ended';
  data: {
    discussionId: string;
    endReason: 'user_ended' | 'max_rounds' | 'no_consensus' | 'host_decided';
    totalRounds: number;
    totalUtterances: number;
    endedAt: string;
  };
}

export interface WsDiscussionControl {
  type: 'discussion_control';
  data: { action: string; message: string };
}

export type WsServerEvent =
  | WsExpertStatus
  | WsUtteranceToken
  | WsUtteranceComplete
  | WsConsensusUpdate
  | WsDiscussionPaused
  | WsDiscussionResumed
  | WsDiscussionEnded
  | WsDiscussionControl;

// ── C→S 事件 ──

export type WsClientCommand =
  | { type: 'advance' }
  | { type: 'pause' }
  | { type: 'resume' }
  | { type: 'end' };
