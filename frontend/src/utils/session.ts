// ── Session ID 生成与管理 ──

const SESSION_KEY = 'ai-panel-studio-session';

export function getSessionId(): string {
  let sid = localStorage.getItem(SESSION_KEY);
  if (!sid) {
    sid = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, sid);
  }
  return sid;
}
