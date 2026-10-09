export default function Layout({ connected, children }) {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-800 bg-slate-950/90 px-6 py-3 backdrop-blur">
        <div className="flex items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-emerald-500/15 text-lg text-emerald-400">
            ◉
          </div>
          <div>
            <h1 className="text-lg font-bold leading-tight">OxeTech Watchers</h1>
            <p className="text-xs text-slate-400">Painel SOC · monitoramento e mitigação</p>
          </div>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-slate-800 px-3 py-1 text-sm">
          <span className={`h-2.5 w-2.5 rounded-full ${connected ? 'animate-pulse bg-emerald-400' : 'bg-red-500'}`} />
          {connected ? 'Ao vivo' : 'Reconectando...'}
        </div>
      </header>
      <main className="mx-auto max-w-7xl space-y-6 p-6">{children}</main>
    </div>
  )
}