import { describe, it, expect, beforeEach } from 'vitest';
import { getSessionId } from '../utils/session';

describe('session — Session ID 管理', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('首次调用生成 UUID', () => {
    const sid = getSessionId();
    expect(sid).toBeTruthy();
    expect(sid.length).toBeGreaterThan(10); // UUID 长度
    expect(localStorage.getItem('ai-panel-studio-session')).toBe(sid);
  });

  it('第二次调用返回相同 ID', () => {
    const sid1 = getSessionId();
    const sid2 = getSessionId();
    expect(sid1).toBe(sid2);
  });

  it('localStorage 不为空时复用已有 ID', () => {
    localStorage.setItem('ai-panel-studio-session', 'existing-session-id');
    expect(getSessionId()).toBe('existing-session-id');
  });
});
