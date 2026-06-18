import { Button } from './ui/Button';

interface ControlBarProps {
  status: 'live' | 'paused' | 'ended';
  currentRound: number;
  totalUtterances: number;
  maxRounds: number | null;
  isCreator: boolean;
  onPause: () => void;
  onResume: () => void;
  onAdvance: () => void;
  onEnd: () => void;
}

export function ControlBar({
  status,
  currentRound,
  totalUtterances,
  maxRounds,
  isCreator,
  onPause,
  onResume,
  onAdvance,
  onEnd,
}: ControlBarProps) {
  const isEnded = status === 'ended';

  return (
    <div className="flex items-center justify-between gap-3 px-4 py-2.5
      bg-[var(--color-studio-elevated)] border-t border-[var(--color-studio-border)] shrink-0">
      {/* left: stats */}
      <div className="flex items-center gap-3 text-xs text-[var(--color-studio-fg-muted)]">
        <span>第 {currentRound} 轮</span>
        <span className="w-1 h-1 rounded-full bg-[var(--color-studio-fg-subtle)]" />
        <span>{totalUtterances} 条发言</span>
        {maxRounds && (
          <>
            <span className="w-1 h-1 rounded-full bg-[var(--color-studio-fg-subtle)]" />
            <span>上限 {maxRounds} 轮</span>
          </>
        )}
      </div>

      {/* right: controls */}
      <div className="flex items-center gap-2">
        {!isEnded && isCreator && (
          <>
            {status === 'live' ? (
              <Button variant="secondary" size="sm" onClick={onPause}>
                暂停
              </Button>
            ) : status === 'paused' ? (
              <Button variant="primary" size="sm" onClick={onResume}>
                继续
              </Button>
            ) : null}
            {status !== 'paused' && (
              <Button variant="secondary" size="sm" onClick={onAdvance}>
                下一轮
              </Button>
            )}
            <Button variant="danger" size="sm" onClick={onEnd}>
              结束
            </Button>
          </>
        )}
        {!isCreator && !isEnded && (
          <span className="text-xs text-[var(--color-studio-fg-muted)]">观看模式</span>
        )}
      </div>
    </div>
  );
}
