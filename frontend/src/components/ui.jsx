export const SEVERITY = {
  low: 'bg-sky-500/15 text-sky-300',
  medium: 'bg-amber-500/15 text-amber-300',
  high: 'bg-orange-500/20 text-orange-300',
  critical: 'bg-red-500/20 text-red-300',
}

export const fmtDate = (iso) => new Date(iso).toLocaleString('pt-BR')

export function Card({ title, right, children, className = '' }) {
  return (
    <section className={`rounded-xl border border-slate-800 bg-slate-900/60 p-4 ${className}`}>
      {(title || right) && (
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold text-slate-200">{title}</h2>
          {right}
        </div>
      )}
      {children}
    </section>
  )
}

export function Stat({ label, value, tone = 'text-slate-100' }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className={`mt-1 text-3xl font-bold ${tone}`}>{value}</p>
    </div>
  )
}

export function Empty({ children }) {
  return <p className="py-6 text-center text-sm text-slate-500">{children}</p>
}