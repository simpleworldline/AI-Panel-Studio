/**
 * Report API — 讨论报告接口
 *
 * GET /api/discussions/:id/report
 *
 * Request:  (无请求体)
 * Response: ApiResponse<DiscussionReport>
 *
 * DiscussionReport:
 *   discussionId  string     讨论ID
 *   topic         string     讨论话题
 *   panel         PanelMember[]  嘉宾阵容
 *   transcript    Utterance[]    完整发言记录
 *   consensus     Consensus[]    共识列表
 *   disagreements Consensus[]    分歧列表
 *   hostSummary   string     主持人总结（最后一条发言内容，可能为空）
 */

import { apiClient } from './client';
import type { ApiResponse, DiscussionReport } from '../types/discussion';

export async function fetchReport(discussionId: string) {
  return apiClient.get<any, ApiResponse<DiscussionReport>>(
    `/discussions/${discussionId}/report`,
  );
}
