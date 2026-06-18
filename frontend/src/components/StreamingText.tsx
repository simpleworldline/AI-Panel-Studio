interface StreamingTextProps {
  text: string;
  isStreaming: boolean;
  memberColor?: string;
}

export function StreamingText({ text, isStreaming, memberColor }: StreamingTextProps) {
  return (
    <span>
      <span>{text}</span>
      {isStreaming && (
        <span
          className="inline-block w-[2px] h-[1em] ml-0.5 align-text-bottom animate-blink-cursor"
          style={{ backgroundColor: memberColor || 'var(--color-studio-fg)' }}
        />
      )}
    </span>
  );
}
