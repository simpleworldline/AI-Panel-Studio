// 共识与分歧类型

export type ConsensusType = 'consensus' | 'disagreement';

export interface ConsensusRecord {
  id: string;
  discussionId: string;
  type: ConsensusType;
  title: string;
  description: string;
  sourceUtteranceIds: string[];
  confidence: number; // 0.0 - 1.0
  isResolved: boolean;
  roundNum: number;
  createdAt: string;
  updatedAt: string;
}
