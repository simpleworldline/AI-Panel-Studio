import { create } from 'zustand';
import type { DiscussionDetail, DiscussionSummary } from '../types/discussion';
import * as api from '../api/discussions';

interface DiscussionStoreState {
  // 列表
  discussions: DiscussionSummary[];
  listLoading: boolean;
  listError: string | null;
  activeTab: 'live' | 'ended' | 'pending';

  // 当前详情
  currentDiscussion: DiscussionDetail | null;
  detailLoading: boolean;
  detailError: string | null;

  // 操作
  fetchList: (status?: 'live' | 'ended' | 'pending') => Promise<void>;
  fetchDetail: (id: string) => Promise<void>;
  clearCurrent: () => void;
  setActiveTab: (tab: 'live' | 'ended' | 'pending') => void;
}

export const useDiscussionStore = create<DiscussionStoreState>((set) => ({
  discussions: [],
  listLoading: false,
  listError: null,
  activeTab: 'live',

  currentDiscussion: null,
  detailLoading: false,
  detailError: null,

  fetchList: async (status) => {
    set({ listLoading: true, listError: null });
    try {
      const res = await api.fetchDiscussions(status);
      set({ discussions: res.data.items, listLoading: false });
    } catch (e: any) {
      set({ listLoading: false, listError: e.message || '加载失败' });
    }
  },

  fetchDetail: async (id) => {
    set({ detailLoading: true, detailError: null, currentDiscussion: null });
    try {
      const res = await api.fetchDiscussionDetail(id);
      set({ currentDiscussion: res.data, detailLoading: false });
    } catch (e: any) {
      set({ detailLoading: false, detailError: e.message || '加载失败' });
    }
  },

  clearCurrent: () =>
    set({ currentDiscussion: null, detailLoading: false, detailError: null }),

  setActiveTab: (activeTab) => set({ activeTab }),
}));
