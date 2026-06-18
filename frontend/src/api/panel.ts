import { apiClient } from './client';
import type {
  ApiResponse,
  PanelGenerateRequest,
  PanelGenerateResponse,
  PanelConfirmRequest,
  PanelMember,
} from '../types/discussion';

// POST /api/discussions/:id/panel/generate
export async function generatePanel(discussionId: string, data: PanelGenerateRequest) {
  return apiClient.post<any, ApiResponse<PanelGenerateResponse>>(
    `/discussions/${discussionId}/panel/generate`,
    data,
  );
}

// PUT /api/discussions/:id/panel
export async function confirmPanel(discussionId: string, data: PanelConfirmRequest) {
  return apiClient.put<
    any,
    ApiResponse<{ discussionId: string; panelConfirmed: boolean; members: PanelMember[] }>
  >(`/discussions/${discussionId}/panel`, data);
}
