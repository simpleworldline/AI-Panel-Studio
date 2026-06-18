import { useEffect, useRef, useMemo } from 'react';
import type { UtteranceDisplay, StreamingUtterance } from '../store/useStudioStore';
import { UtteranceItem } from './UtteranceItem';
import { StreamingText } from './StreamingText';
import { EmptyState } from './EmptyState';

interface TranscriptViewProps {
  utterances: UtteranceDisplay[];
  streaming: StreamingUtterance | null;
}

/** Group utterances into root + children for threaded view */
function groupThreads(utterances: UtteranceDisplay[]): { roots: string[]; childrenOf: Record<string, UtteranceDisplay[]> } {
  const roots: string[] = [];
  const childrenOf: Record<string, UtteranceDisplay[]> = {};
  for (const u of utterances) {
    const pid = u.parentUtteranceId;
    if (pid && utterances.some((r) => r.id === pid)) {
      (childrenOf[pid] ||= []).push(u);
    } else {
      roots.push(u.id);
    }
  }
  return { roots, childrenOf };
}

export function TranscriptView({ utterances, streaming }: TranscriptViewProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [utterances.length, streaming?.accumulatedText]);

  const { roots, childrenOf } = useMemo(() => groupThreads(utterances), [utterances]);
  const idMap = useMemo(() => {
    const m: Record<string, UtteranceDisplay> = {};
    for (const u of utterances) m[u.id] = u;
    return m;
  }, [utterances]);

  if (utterances.length === 0 && !streaming) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <EmptyState
          title="等待讨论开始"
          description="嘉宾正在准备中，发言将在此实时展示"
          icon={
            <svg className="w-12 h-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
            </svg>
          }
        />
      </div>
    );
  }

  const renderUtterance = (uid: string, isChild: boolean) => {
    const u = idMap[uid];
    if (!u) return null;
    const kids = childrenOf[uid];
    return (
      <div key={uid}>
        <UtteranceItem utterance={u} isChild={isChild} />
        {kids && kids.map((kid) => (
          <div key={kid.id} className="ml-10 pl-4 border-l-2 border-[var(--color-studio-border)]">
            <UtteranceItem utterance={kid} isChild />
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="flex-1 overflow-y-auto py-2">
      {/* Render roots with their nested children */}
      {roots.map((rid) => renderUtterance(rid, false))}

      {/* Streaming utterance */}
      {streaming && (
        <div className={`flex gap-3 px-4 py-3 ${streaming.parentUtteranceId ? 'ml-10 pl-4 border-l-2 border-[var(--color-studio-border)]' : ''}`}>
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0 mt-0.5"
            style={{ backgroundColor: streaming.memberColor }}
          >
            {streaming.memberName.charAt(0)}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold" style={{ color: streaming.memberColor }}>
                {streaming.memberName}
              </span>
              <span className="text-[10px] text-[var(--color-studio-fg-subtle)]">
                {streaming.memberTitle}
              </span>
              <span
                className="text-[10px] px-1.5 py-0.5 rounded animate-status-pulse"
                style={{ backgroundColor: streaming.memberColor + '18', color: streaming.memberColor }}
              >
                发言中
              </span>
            </div>
            <p className="text-sm text-[var(--color-studio-fg)] leading-relaxed whitespace-pre-wrap break-words">
              <StreamingText
                text={streaming.accumulatedText}
                isStreaming={streaming.isStreaming}
                memberColor={streaming.memberColor}
              />
            </p>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
