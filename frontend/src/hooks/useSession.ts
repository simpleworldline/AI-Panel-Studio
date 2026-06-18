import { getSessionId } from '../utils/session';

export function useSession() {
  return { sessionId: getSessionId() };
}
