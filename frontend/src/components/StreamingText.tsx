interface StreamingTextProps {
  content: string;
  isStreaming: boolean;
  memberColor: string;
}

export function StreamingText({ content, isStreaming, memberColor }: StreamingTextProps) {
  return (
    <span style={{ color: memberColor }}>
      {content}
      {isStreaming && (
        <span
          className="inline-block ml-0.5 text-[var(--color-studio-accent)]"
          style={{ animation: 'blink-cursor 1s step-end infinite' }}
        >
          ▍
        </span>
      )}
    </span>
  );
}
