import { apiClient } from './client';
import type {
  ApiResponse,
  PaginatedList,
  Discussion,
  DiscussionDetail,
  DiscussionSummary,
  DiscussionReport,
  CreateDiscussionRequest,
} from '../types/discussion';

// GET /api/discussions
export async function fetchDiscussions(status?: 'live' | 'ended' | 'pending', page = 1, pageSize = 50) {
  const params: Record<string, string | number> = { page, pageSize };
  if (status) params.status = status;
  return apiClient.get<any, ApiResponse<PaginatedList<DiscussionSummary>>>('/discussions', { params });
}

// POST /api/discussions
export async function createDiscussion(data: CreateDiscussionRequest) {
  return apiClient.post<any, ApiResponse<Discussion>>('/discussions', data);
}

// GET /api/discussions/:id
export async function fetchDiscussionDetail(id: string) {
  return apiClient.get<any, ApiResponse<DiscussionDetail>>(`/discussions/${id}`);
}

// POST /api/discussions/:id/start
export async function startDiscussion(id: string) {
  return apiClient.post<any, ApiResponse<{ discussionId: string; status: string }>>(
    `/discussions/${id}/start`,
  );
}

// POST /api/discussions/:id/pause
export async function pauseDiscussion(id: string) {
  return apiClient.post<any, ApiResponse<{ discussionId: string; status: string }>>(
    `/discussions/${id}/pause`,
  );
}

// POST /api/discussions/:id/resume
export async function resumeDiscussion(id: string) {
  return apiClient.post<any, ApiResponse<{ discussionId: string; status: string }>>(
    `/discussions/${id}/resume`,
  );
}

// POST /api/discussions/:id/next
export async function advanceDiscussion(id: string) {
  return apiClient.post<any, ApiResponse<{ discussionId: string; roundTriggered: boolean }>>(
    `/discussions/${id}/next`,
  );
}

// POST /api/discussions/:id/end
export async function endDiscussion(id: string) {
  return apiClient.post<
    any,
    ApiResponse<{
      discussionId: string;
      status: string;
      endedAt: string;
      totalRounds: number;
      totalUtterances: number;
    }>
  >(`/discussions/${id}/end`);
}

// GET /api/discussions/:id/report
export async function fetchDiscussionReport(id: string) {
  return apiClient.get<any, ApiResponse<DiscussionReport>>(`/discussions/${id}/report`);
}
