import { useEffect, useRef } from 'react';
import type { UtteranceDisplay, StreamingUtterance } from '../store/useStudioStore';
import { UtteranceItem } from './UtteranceItem';
import { StreamingText } from './StreamingText';
import { EmptyState } from './EmptyState';

interface TranscriptViewProps {
  utterances: UtteranceDisplay[];
  streaming: StreamingUtterance | null;
}

export function TranscriptView({ utterances, streaming }: TranscriptViewProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [utterances.length, streaming?.accumulatedText]);

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

  return (
    <div className="flex-1 overflow-y-auto py-2">
      {utterances.map((u) => (
        <UtteranceItem key={u.id} utterance={u} />
      ))}

      {/* 流式发言 */}
      {streaming && (
        <div className="flex gap-3 px-4 py-3">
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
