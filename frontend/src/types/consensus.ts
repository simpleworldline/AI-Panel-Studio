// ── 共识/分歧显示类型 ──

export type ConsensusType = 'consensus' | 'disagreement';

export interface ConsensusItemDisplay {
  id: string;
  type: ConsensusType;
  title: string;
  description: string;
  sourceUtteranceIds: string[];
  confidence: number;
  isResolved: boolean;
  roundNum: number;
}
