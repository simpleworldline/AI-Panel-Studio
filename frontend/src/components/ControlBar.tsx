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
  if (!isCreator) {
    return (
      <div className="flex items-center justify-center py-2 px-5 bg-[var(--color-studio-elevated)] border-t border-[var(--color-studio-border)]">
        <span className="text-xs text-[var(--color-studio-fg-dim)]">
          观看中 · 轮次 {currentRound}/{maxRounds || '∞'} · 发言 {totalUtterances} 条
        </span>
      </div>
    );
  }

  const showPause = status === 'live';
  const showResume = status === 'paused';
  const showControls = status !== 'ended';

  return (
    <div className="flex items-center justify-center gap-3 py-2 px-5 bg-[var(--color-studio-elevated)] border-t border-[var(--color-studio-border)] flex-wrap">
      {showControls && (
        <>
          {showPause && (
            <Button variant="secondary" size="sm" onClick={onPause}>
              ⏸ 暂停
            </Button>
          )}
          {showResume && (
            <Button variant="primary" size="sm" onClick={onResume}>
              ▶ 继续
            </Button>
          )}
          <Button variant="primary" size="sm" onClick={onAdvance}>
            ▶ 下一轮
          </Button>
          <Button variant="danger" size="sm" onClick={onEnd}>
            ⏹ 结束讨论
          </Button>
        </>
      )}
      <span className="text-[11px] text-[var(--color-studio-fg-dim)] ml-2">
        轮次 {currentRound}/{maxRounds || '∞'} · 发言 {totalUtterances} 条
      </span>
    </div>
  );
}
