import { create } from 'zustand';
import type {
  DiscussionSummary,
  DiscussionDetail,
  CreateDiscussionRequest,
} from '../types/discussion';
import {
  fetchDiscussions,
  createDiscussion,
  fetchDiscussionDetail,
} from '../api/discussions';

interface DiscussionStoreState {
  liveDiscussions: DiscussionSummary[];
  endedDiscussions: DiscussionSummary[];
  listLoading: boolean;
  listError: string | null;

  currentDiscussion: DiscussionDetail | null;
  detailLoading: boolean;
  detailError: string | null;

  fetchList: () => Promise<void>;
  fetchDetail: (id: string) => Promise<void>;
  createNew: (data: CreateDiscussionRequest) => Promise<string>;
  clearCurrent: () => void;
}

export const useDiscussionStore = create<DiscussionStoreState>((set) => ({
  liveDiscussions: [],
  endedDiscussions: [],
  listLoading: false,
  listError: null,

  currentDiscussion: null,
  detailLoading: false,
  detailError: null,

  fetchList: async () => {
    set({ listLoading: true, listError: null });
    try {
      const [liveRes, endedRes] = await Promise.all([
        fetchDiscussions('live'),
        fetchDiscussions('ended'),
      ]);
      set({
        liveDiscussions: liveRes.data.items,
        endedDiscussions: endedRes.data.items,
        listLoading: false,
      });
    } catch (e: any) {
      set({ listError: e.message, listLoading: false });
    }
  },

  fetchDetail: async (id: string) => {
    set({ detailLoading: true, detailError: null });
    try {
      const res = await fetchDiscussionDetail(id);
      set({ currentDiscussion: res.data, detailLoading: false });
    } catch (e: any) {
      set({ detailError: e.message, detailLoading: false });
    }
  },

  createNew: async (data: CreateDiscussionRequest) => {
    const res = await createDiscussion(data);
    return res.data.id;
  },

  clearCurrent: () => {
    set({ currentDiscussion: null, detailError: null });
  },
}));
