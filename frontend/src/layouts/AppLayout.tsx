import { Outlet, Link, useLocation } from 'react-router-dom';

export function AppLayout() {
  const location = useLocation();
  const isHome = location.pathname === '/';

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Top Bar */}
      <header className="flex items-center justify-between py-2.5 px-5 bg-[var(--color-studio-elevated)] border-b border-[var(--color-studio-border)] flex-shrink-0 gap-4">
        <Link to="/" className="flex items-center gap-2.5 font-[var(--font-heading)] font-bold text-base tracking-tight no-underline whitespace-nowrap">
          <span className="w-2.5 h-2.5 rounded-full bg-[var(--color-studio-accent)] shadow-[0_0_12px_rgba(34,197,94,0.3)] animate-[pulse-dot_2s_ease-in-out_infinite]" />
          AI Panel Studio
        </Link>
        {!isHome && (
          <span className="flex-1 text-center text-sm text-[var(--color-studio-fg-muted)] truncate" />
        )}
        <nav className="flex items-center gap-6">
          <Link
            to="/"
            className={`text-sm font-medium no-underline transition-colors duration-200 ${isHome ? 'text-[var(--color-studio-fg)]' : 'text-[var(--color-studio-fg-muted)] hover:text-[var(--color-studio-fg)]'}`}
          >
            讨论广场
          </Link>
        </nav>
      </header>

      {/* Page Content */}
      <Outlet />
    </div>
  );
}
