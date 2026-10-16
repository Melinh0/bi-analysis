export function formatarNumero(valor?: number | null): string {
  if (valor === null || valor === undefined) return '—';
  const n = Number(valor);
  if (!Number.isFinite(n)) return '—';
  if (Math.abs(n) >= 1e9) return (n / 1e9).toFixed(1).replace('.', ',') + ' bi';
  if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(1).replace('.', ',') + ' mi';
  if (Math.abs(n) >= 1e3) return (n / 1e3).toFixed(1).replace('.', ',') + ' mil';
  return String(Math.round(n * 100) / 100).replace('.', ',');
}

export function formatarTaxa(valor?: number | null): string {
  if (valor === null || valor === undefined || !Number.isFinite(Number(valor))) return '—';
  return (Number(valor) * 100).toFixed(2).replace('.', ',') + '%';
}

interface PontoBarras {
  rotulo: string;
  valor: number;
  cor?: string;
}

export function GraficoBarras({ dados, titulo }: { dados: PontoBarras[]; titulo: string }) {
  const maximo = Math.max(...dados.map((d) => d.valor), 1);

  return (
    <div className="rounded-xl border border-dark-200 bg-white p-4">
      <h3 className="mb-3 text-sm font-semibold text-dark-900">{titulo}</h3>
      {dados.length === 0 ? (
        <p className="py-8 text-center text-xs text-dark-400">Sem dados para exibir</p>
      ) : (
        <div className="flex h-52 items-end gap-2">
          {dados.map((d, i) => (
            <div key={i} className="flex min-w-0 flex-1 flex-col items-center gap-1">
              <span className="text-[10px] font-medium text-dark-500">{formatarNumero(d.valor)}</span>
              <div
                className="w-full rounded-t-md transition-all"
                style={{
                  height: `${Math.max((d.valor / maximo) * 100, 1)}%`,
                  background: d.cor || '#6366f1',
                }}
              />
              <span
                className="block w-full truncate text-center text-[10px] text-dark-400"
                title={d.rotulo}
              >
                {d.rotulo}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

interface PontoLinha {
  rotulo: string;
  valor: number;
}

export function GraficoLinha({ dados, titulo, cor = '#0ea5e9' }: { dados: PontoLinha[]; titulo: string; cor?: string }) {
  const L = 720;
  const A = 200;
  const margem = 24;
  const maximo = Math.max(...dados.map((d) => d.valor), 1);
  const pontos = dados.map((d, i) => ({
    x: margem + (dados.length === 1 ? 0 : (i * (L - 2 * margem)) / (dados.length - 1)),
    y: A - margem - (d.valor / maximo) * (A - 2 * margem),
    ...d,
  }));
  const linha = pontos.map((p) => `${p.x},${p.y}`).join(' ');
  const area =
    pontos.length > 0
      ? `${pontos[0].x},${A - margem} ${linha} ${pontos[pontos.length - 1].x},${A - margem}`
      : '';
  const passo = Math.max(1, Math.ceil(pontos.length / 8));

  return (
    <div className="rounded-xl border border-dark-200 bg-white p-4">
      <h3 className="mb-3 text-sm font-semibold text-dark-900">{titulo}</h3>
      {pontos.length === 0 ? (
        <p className="py-8 text-center text-xs text-dark-400">Sem série temporal disponível</p>
      ) : (
        <svg viewBox={`0 0 ${L} ${A}`} className="w-full" role="img" aria-label={titulo}>
          <line x1={margem} y1={A - margem} x2={L - margem} y2={A - margem} stroke="#e2e8f0" />
          <line x1={margem} y1={margem} x2={margem} y2={A - margem} stroke="#e2e8f0" />
          {area && <polygon points={area} fill={cor} opacity={0.12} />}
          <polyline points={linha} fill="none" stroke={cor} strokeWidth={2} />
          {pontos.map((p, i) => (
            <circle key={i} cx={p.x} cy={p.y} r={2.5} fill={cor} />
          ))}
          {pontos.map((p, i) =>
            i % passo === 0 ? (
              <text
                key={`t${i}`}
                x={p.x}
                y={A - 6}
                fontSize={10}
                fill="#94a3b8"
                textAnchor="middle"
              >
                {p.rotulo.slice(5)}
              </text>
            ) : null
          )}
          <text x={margem} y={margem - 6} fontSize={10} fill="#94a3b8">
            máx {formatarNumero(maximo)}
          </text>
        </svg>
      )}
    </div>
  );
}
