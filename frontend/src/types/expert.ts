// 专家状态类型

export type ExpertStatusKind = 'idle' | 'preparing' | 'speaking';

/** WebSocket expert_status 事件推送的专家状态 */
export interface ExpertStatus {
  memberId: string;
  status: ExpertStatusKind;
  focusSummary: string | null;
  desireValue: number; // 0.00 - 1.00
  timestamp: string;
}
