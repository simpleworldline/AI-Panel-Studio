// ── 讨论 & 嘉宾 核心类型 (对齐 API_CONTRACT.md) ──

export type DiscussionStatus = 'pending' | 'live' | 'paused' | 'ended';
export type MemberRole = 'host' | 'expert';
export type UtteranceType = 'opening' | 'statement' | 'question' | 'reply' | 'summary';

export interface PanelMember {
  id: string;
  name: string;
  title: string;
  role: MemberRole;
  stance: string;
  color: string;
  avatarPrompt?: string;
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

export interface ConsensusRecord {
  id: string;
  type: 'consensus' | 'disagreement';
  title: string;
  description: string;
  sourceUtteranceIds: string[];
  confidence: number;
  isResolved: boolean;
  roundNum: number;
}

export interface Discussion {
  id: string;
  topic: string;
  expertCount: number;
  maxRounds: number | null;
  status: DiscussionStatus;
  creatorSessionId: string;
  currentRound: number;
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
  memberPreview: Array<{ name: string; role: MemberRole }>;
}

export interface DiscussionDetail {
  id: string;
  topic: string;
  expertCount: number;
  status: DiscussionStatus;
  currentRound: number;
  maxRounds: number | null;
  createdAt: string;
  endedAt: string | null;
  creatorSessionId: string;
  panel: PanelMember[];
  transcript: Utterance[];
  consensus: ConsensusRecord[];
  disagreements: ConsensusRecord[];
}

export interface DiscussionReport {
  discussionId: string;
  topic: string;
  panel: PanelMember[];
  transcript: Utterance[];
  consensus: ConsensusRecord[];
  disagreements: ConsensusRecord[];
  hostSummary: string;
}

// ── API 请求体 ──

export interface CreateDiscussionRequest {
  topic: string;
  expertCount: number;
  maxRounds?: number | null;
}

export interface PanelGenerateRequest {
  regenerateMemberId: string | null;
}

export interface PanelGenerateResponse {
  host: Omit<PanelMember, 'id' | 'role'>;
  experts: Array<Omit<PanelMember, 'id' | 'role'>>;
}

export interface PanelConfirmRequest {
  host: Omit<PanelMember, 'id' | 'role'>;
  experts: Array<Omit<PanelMember, 'id' | 'role'>>;
}

// ── API 通用响应 ──

export interface ApiResponse<T> {
  code: number;
  data: T;
  message: string;
  detail?: string;
}

export interface PaginatedList<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}
