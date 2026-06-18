// ── 专家状态类型 ──

export type ExpertStatusKind = 'idle' | 'preparing' | 'speaking';

export interface ExpertStatus {
  memberId: string;
  memberName: string;
  memberColor: string;
  status: ExpertStatusKind;
  focusSummary: string | null;
  desireValue: number;
  timestamp: string;
}
