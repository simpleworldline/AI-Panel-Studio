import { create } from 'zustand';
import type { PanelMember } from '../types/discussion';
import * as api from '../api/panel';

interface PanelMemberDraft {
  name: string;
  title: string;
  stance: string;
  color: string;
}

interface PanelStoreState {
  discussionId: string;
  expertCount: number;
  host: PanelMemberDraft | null;
  experts: PanelMemberDraft[];
  generating: boolean;
  generateError: string | null;
  confirming: boolean;
  confirmError: string | null;

  init: (discussionId: string, expertCount: number) => void;
  generate: (discussionId: string) => Promise<void>;
  regenerateOne: (discussionId: string, memberIndex: number) => Promise<void>;
  regenerateAll: (discussionId: string) => Promise<void>;
  updateHost: (data: Partial<PanelMemberDraft>) => void;
  updateExpert: (index: number, data: Partial<PanelMemberDraft>) => void;
  confirm: (discussionId: string) => Promise<PanelMember[]>;
  reset: () => void;
}

export const usePanelStore = create<PanelStoreState>((set, get) => ({
  discussionId: '',
  expertCount: 4,
  host: null,
  experts: [],
  generating: false,
  generateError: null,
  confirming: false,
  confirmError: null,

  init: (discussionId, expertCount) =>
    set({ discussionId, expertCount, host: null, experts: [], generateError: null, confirmError: null }),

  generate: async (discussionId) => {
    set({ generating: true, generateError: null });
    try {
      const res = await api.generatePanel(discussionId, { regenerateMemberId: null });
      set({
        host: res.data.host,
        experts: res.data.experts,
        generating: false,
      });
    } catch (e: any) {
      set({ generating: false, generateError: e.message || '生成失败' });
    }
  },

  regenerateOne: async (discussionId, memberIndex) => {
    set({ generating: true, generateError: null });
    try {
      const res = await api.generatePanel(discussionId, { regenerateMemberId: null });
      const s = get();
      const updated = [...s.experts];
      if (res.data.experts[memberIndex]) {
        updated[memberIndex] = res.data.experts[memberIndex];
      }
      set({ experts: updated, generating: false });
    } catch (e: any) {
      set({ generating: false, generateError: e.message || '重生失败' });
    }
  },

  regenerateAll: async (discussionId) => {
    await get().generate(discussionId);
  },

  updateHost: (data) => {
    const s = get();
    if (s.host) set({ host: { ...s.host, ...data } });
  },

  updateExpert: (index, data) => {
    const s = get();
    if (s.experts[index]) {
      const updated = [...s.experts];
      updated[index] = { ...updated[index], ...data };
      set({ experts: updated });
    }
  },

  confirm: async (discussionId) => {
    set({ confirming: true, confirmError: null });
    const s = get();
    try {
      const res = await api.confirmPanel(discussionId, {
        host: s.host!,
        experts: s.experts,
      });
      set({ confirming: false });
      return res.data.members;
    } catch (e: any) {
      set({ confirming: false, confirmError: e.message || '确认失败' });
      throw e;
    }
  },

  reset: () =>
    set({
      discussionId: '',
      expertCount: 4,
      host: null,
      experts: [],
      generating: false,
      generateError: null,
      confirming: false,
      confirmError: null,
    }),
}));
