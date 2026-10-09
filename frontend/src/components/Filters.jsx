const input =
  'w-full rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm outline-none focus:border-emerald-500'

export default function Filters({ value, onChange, attackTypes = [] }) {
  const set = (k) => (e) => onChange({ ...value, [k]: e.target.value })
  const empty = { ip: '', attack_type: '', start: '', end: '' }

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
      <label className="text-xs text-slate-400">
        IP (atacante ou vítima)
        <input className={input} placeholder="192.168.0.50" value={value.ip} onChange={set('ip')} />
      </label>
      <label className="text-xs text-slate-400">
        Tipo de ataque
        <input className={input} list="attack-types" placeholder="brute_force_rdp" value={value.attack_type} onChange={set('attack_type')} />
        <datalist id="attack-types">
          {attackTypes.map((t) => <option key={t} value={t} />)}
        </datalist>
      </label>
      <label className="text-xs text-slate-400">
        De
        <input type="datetime-local" className={input} value={value.start} onChange={set('start')} />
      </label>
      <label className="text-xs text-slate-400">
        Até
        <input type="datetime-local" className={input} value={value.end} onChange={set('end')} />
      </label>
      <div className="flex items-end">
        <button
          onClick={() => onChange(empty)}
          className="w-full rounded-md border border-slate-700 px-3 py-1.5 text-sm hover:bg-slate-800"
        >
          Limpar filtros
        </button>
      </div>
    </div>
  )
}