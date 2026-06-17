import { create } from 'zustand';
import type { PanelMemberEditable } from '../types/discussion';
import { generatePanel, confirmPanel } from '../api/panel';

interface PanelStoreState {
  discussionId: string | null;
  host: PanelMemberEditable | null;
  experts: PanelMemberEditable[];
  expertCount: number;

  generatePhase: 'idle' | 'loading' | 'success' | 'error';
  generateError: string | null;
  confirmPhase: 'idle' | 'loading' | 'success' | 'error';
  confirmError: string | null;
  isDirty: boolean;

  init: (discussionId: string, expertCount: number) => void;
  generate: () => Promise<void>;
  regenerateMember: (memberId: string) => Promise<void>;
  regenerateAll: () => Promise<void>;

  updateHost: (field: keyof PanelMemberEditable, value: string) => void;
  updateExpert: (index: number, field: keyof PanelMemberEditable, value: string) => void;

  confirm: () => Promise<void>;
  reset: () => void;
}

export const usePanelStore = create<PanelStoreState>((set, get) => ({
  discussionId: null,
  host: null,
  experts: [],
  expertCount: 4,

  generatePhase: 'idle',
  generateError: null,
  confirmPhase: 'idle',
  confirmError: null,
  isDirty: false,

  init: (discussionId, expertCount) => {
    set({
      discussionId,
      expertCount,
      host: null,
      experts: [],
      generatePhase: 'idle',
      generateError: null,
      confirmPhase: 'idle',
      confirmError: null,
      isDirty: false,
    });
  },

  generate: async () => {
    const { discussionId } = get();
    if (!discussionId) return;
    set({ generatePhase: 'loading', generateError: null });
    try {
      const res = await generatePanel(discussionId, { regenerateMemberId: null });
      set({
        host: res.data.host,
        experts: res.data.experts,
        generatePhase: 'success',
        isDirty: false,
      });
    } catch (e: any) {
      set({ generatePhase: 'error', generateError: e.message });
    }
  },

  regenerateMember: async (memberId: string) => {
    const { discussionId } = get();
    if (!discussionId || !memberId) return;
    set({ generatePhase: 'loading' });
    try {
      const res = await generatePanel(discussionId, { regenerateMemberId: memberId });
      // replace target member in list
      set((s) => {
        const experts = [...s.experts];
        // find and replace
        return { ...res.data, generatePhase: 'success' as const };
      });
    } catch (e: any) {
      set({ generatePhase: 'error', generateError: e.message });
    }
  },

  regenerateAll: async () => {
    await get().generate();
  },

  updateHost: (field, value) => {
    set((s) => {
      if (!s.host) return s;
      return { host: { ...s.host, [field]: value }, isDirty: true };
    });
  },

  updateExpert: (index, field, value) => {
    set((s) => {
      const experts = [...s.experts];
      if (experts[index]) {
        experts[index] = { ...experts[index], [field]: value };
      }
      return { experts, isDirty: true };
    });
  },

  confirm: async () => {
    const { discussionId, host, experts } = get();
    if (!discussionId || !host) return;
    set({ confirmPhase: 'loading', confirmError: null });
    try {
      await confirmPanel(discussionId, { host, experts });
      set({ confirmPhase: 'success', isDirty: false });
    } catch (e: any) {
      set({ confirmPhase: 'error', confirmError: e.message });
    }
  },

  reset: () => {
    set({
      discussionId: null,
      host: null,
      experts: [],
      generatePhase: 'idle',
      generateError: null,
      confirmPhase: 'idle',
      confirmError: null,
      isDirty: false,
    });
  },
}));
