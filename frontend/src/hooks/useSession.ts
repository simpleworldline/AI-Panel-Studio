import { useMemo } from 'react';
import { getSessionId } from '../utils/session';

export function useSession() {
  const sessionId = useMemo(() => getSessionId(), []);
  return { sessionId };
}
