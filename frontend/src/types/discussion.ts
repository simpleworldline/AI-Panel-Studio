// ============================================================
// Discussion / PanelMember / Utterance — 核心实体类型
// 与 API_CONTRACT.md 对齐
// ============================================================

export type DiscussionStatus = 'pending' | 'live' | 'paused' | 'ended';
export type PanelRole = 'host' | 'expert';
export type UtteranceType =
  | 'opening'
  | 'statement'
  | 'rebuttal'
  | 'supplement'
  | 'question'
  | 'summary';

export interface Discussion {
  id: string;
  topic: string;
  expertCount: number;
  maxRounds: number | null;
  status: DiscussionStatus;
  creatorSessionId: string;
  currentRound: number;
  roundsWithoutConsensus: number;
  autoEndThreshold: number;
  createdAt: string;
  endedAt: string | null;
}

export interface DiscussionSummary {
  id: string;
  topic: string;
  expertCount: number;
  status: DiscussionStatus;
  currentRound: number;
  createdAt: string;
  memberPreview: { name: string; role: PanelRole; color: string }[];
}

export interface DiscussionDetail extends Discussion {
  panel: PanelMember[];
  transcript: UtteranceResponse[];
  consensus: ConsensusRecord[];
  disagreements: ConsensusRecord[];
}

export interface PanelMember {
  id: string;
  discussionId: string;
  name: string;
  title: string;
  role: PanelRole;
  stance: string;
  color: string;
  avatarPrompt: string | null;
  sortOrder: number;
}

/** 嘉宾编辑时使用（不含 id/discussionId，可修改字段） */
export interface PanelMemberEditable {
  id?: string;
  name: string;
  title: string;
  role: PanelRole;
  stance: string;
  color: string;
}

export interface UtteranceResponse {
  id: string;
  panelMemberId: string;
  memberName: string;
  memberTitle: string;
  memberColor: string;
  content: string;
  utteranceType: UtteranceType;
  sequenceNum: number;
  roundNum: number;
  isStreaming: boolean;
  createdAt: string;
}

export interface Utterance {
  id: string;
  panelMemberId: string;
  memberName: string;
  memberTitle: string;
  memberColor: string;
  content: string;
  utteranceType: UtteranceType;
  sequenceNum: number;
  roundNum: number;
  createdAt: string;
}

// ── Request types ──

export interface CreateDiscussionRequest {
  topic: string;
  expertCount: number;
  maxRounds: number | null;
}

export interface PanelGenerateRequest {
  regenerateMemberId: string | null;
}

export interface PanelGenerateResponse {
  host: PanelMemberEditable;
  experts: PanelMemberEditable[];
}

export interface PanelConfirmRequest {
  host: PanelMemberEditable;
  experts: PanelMemberEditable[];
}

export interface DiscussionReport {
  discussionId: string;
  topic: string;
  panel: PanelMember[];
  transcript: UtteranceResponse[];
  consensus: ConsensusRecord[];
  disagreements: ConsensusRecord[];
  hostSummary: string;
}

// ── API response wrapper ──

export interface ApiResponse<T> {
  code: number;
  data: T;
  message: string;
}

export interface PaginatedList<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}
