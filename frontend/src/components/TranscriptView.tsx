import { useRef, useEffect } from 'react';
import type { UtteranceDisplay, StreamingUtterance } from '../store/useStudioStore';
import { UtteranceItem } from './UtteranceItem';
import { StreamingText } from './StreamingText';

interface TranscriptViewProps {
  utterances: UtteranceDisplay[];
  streaming: StreamingUtterance | null;
  readonly?: boolean;
}

export function TranscriptView({ utterances, streaming, readonly = false }: TranscriptViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const shouldAutoScroll = useRef(true);

  // Auto-scroll to bottom when new utterances arrive or streaming updates
  useEffect(() => {
    if (shouldAutoScroll.current && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [utterances.length, streaming?.accumulatedText]);

  // Detect manual scroll
  const handleScroll = () => {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    shouldAutoScroll.current = scrollTop + clientHeight >= scrollHeight - 100;
  };

  return (
    <div ref={containerRef} className="flex-1 overflow-y-auto p-3" onScroll={handleScroll}>
      <div className="flex flex-col gap-1">
        {utterances.map((u) => (
          <UtteranceItem key={u.id} utterance={u} />
        ))}

        {/* Streaming utterance */}
        {!readonly && streaming && (
          <div className="flex gap-3 px-4 py-3.5 rounded-[var(--radius-sm)]">
            <div
              className="w-[3px] rounded-[2px] flex-shrink-0 self-stretch"
              style={{ backgroundColor: streaming.memberColor }}
            />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-semibold text-sm" style={{ color: streaming.memberColor }}>
                  {streaming.memberName}
                </span>
                <span className="text-[11px] text-[var(--color-studio-fg-dim)]">{streaming.memberTitle}</span>
                <span className="text-[10px] font-semibold tracking-wider uppercase px-[6px] py-[1px] rounded-[3px] bg-white/5 text-[var(--color-studio-fg-dim)]">
                  发言
                </span>
              </div>
              <p className="text-sm leading-relaxed">
                <StreamingText
                  content={streaming.accumulatedText}
                  isStreaming={streaming.isStreaming}
                  memberColor={streaming.memberColor}
                />
              </p>
              <div className="mt-1.5 text-[10px] text-[var(--color-studio-accent)] font-[var(--font-heading)]">
                ● 实时发言中...
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
