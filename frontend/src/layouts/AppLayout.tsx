import { Outlet, useNavigate } from 'react-router-dom';

export function AppLayout() {
  const navigate = useNavigate();

  return (
    <div className="h-full overflow-hidden flex flex-col bg-[var(--color-studio-bg)]">
      {/* header */}
      <header className="flex items-center justify-between px-6 py-3
        bg-[var(--color-studio-elevated)] border-b border-[var(--color-studio-border)] shrink-0">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2.5 cursor-pointer hover:opacity-80 transition-opacity"
        >
          <svg className="w-6 h-6 text-[var(--color-studio-gold)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
          <span className="text-sm font-bold tracking-wider text-[var(--color-studio-fg)]">
            AI Panel Studio
          </span>
        </button>

        <div className="flex items-center gap-3">
          <span className="text-[11px] text-[var(--color-studio-fg-muted)]">
            AI 演播厅
          </span>
        </div>
      </header>

      {/* content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
