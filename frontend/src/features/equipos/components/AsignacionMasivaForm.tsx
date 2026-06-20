import { useState } from 'react';
import { useAsignacionMasiva } from '@/features/equipos/hooks/useEquipoMutations';
import { useRoles } from '@/features/equipos/hooks/useEquipos';
import { useCarreras, useCohortes, useMaterias } from '@/features/estructura/hooks/useEstructura';
import { useUsuarios } from '@/features/admin/hooks/useUsuarios';
import type { AsignacionMasivaResult } from '@/features/equipos/types';

// ── Paso 1: Contexto del equipo ──────────────────────────────────────────────

interface ContextoForm {
  materia_id: string;
  carrera_id: string;
  cohorte_id: string;
}

function PasoContexto({
  value,
  onChange,
  onNext,
}: {
  value: ContextoForm;
  onChange: (v: ContextoForm) => void;
  onNext: () => void;
}) {
  const { data: materias = [], isLoading: loadingMaterias } = useMaterias();
  const { data: carreras = [], isLoading: loadingCarreras } = useCarreras();
  const { data: cohortes = [], isLoading: loadingCohortes } = useCohortes();

  const canNext = value.materia_id || value.carrera_id || value.cohorte_id;

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Paso 1: Contexto del equipo</h2>
      <p className="text-sm text-gray-500">
        Seleccioná al menos un campo para delimitar el equipo. Podés dejar campos vacíos.
      </p>

      <div>
        <label className="block text-sm font-medium text-gray-700">Materia</label>
        <select
          value={value.materia_id}
          onChange={(e) => onChange({ ...value, materia_id: e.target.value })}
          disabled={loadingMaterias}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:bg-gray-50 disabled:text-gray-400"
        >
          <option value="">— Sin filtro —</option>
          {materias.map((m) => (
            <option key={m.id} value={m.id}>{m.nombre}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Carrera</label>
        <select
          value={value.carrera_id}
          onChange={(e) => onChange({ ...value, carrera_id: e.target.value })}
          disabled={loadingCarreras}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:bg-gray-50 disabled:text-gray-400"
        >
          <option value="">— Sin filtro —</option>
          {carreras.map((c) => (
            <option key={c.id} value={c.id}>{c.nombre}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Cohorte</label>
        <select
          value={value.cohorte_id}
          onChange={(e) => onChange({ ...value, cohorte_id: e.target.value })}
          disabled={loadingCohortes}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:bg-gray-50 disabled:text-gray-400"
        >
          <option value="">— Sin filtro —</option>
          {cohortes.map((c) => (
            <option key={c.id} value={c.id}>{c.etiqueta}</option>
          ))}
        </select>
      </div>

      <button
        type="button"
        onClick={onNext}
        disabled={!canNext}
        className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-40"
      >
        Siguiente
      </button>
    </div>
  );
}

// ── Paso 2: Selección de docentes ────────────────────────────────────────────

function PasoDocentes({
  selected,
  onToggle,
  onNext,
  onPrev,
}: {
  selected: string[];
  onToggle: (id: string) => void;
  onNext: () => void;
  onPrev: () => void;
}) {
  const [q, setQ] = useState('');
  const { data: usuarios = [], isLoading } = useUsuarios({ q: q || undefined });

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Paso 2: Selección de docentes</h2>
      <p className="text-sm text-gray-500">
        Buscá y seleccioná los docentes a asignar ({selected.length} seleccionados).
      </p>

      <input
        type="search"
        placeholder="Buscar por nombre, apellido o legajo…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
      />

      <div className="max-h-72 overflow-y-auto rounded-md border border-gray-200">
        {isLoading && (
          <p className="px-4 py-3 text-sm text-gray-400">Cargando…</p>
        )}
        {!isLoading && usuarios.length === 0 && (
          <p className="px-4 py-3 text-sm text-gray-400">Sin resultados.</p>
        )}
        {usuarios.map((u) => (
          <label
            key={u.id}
            className="flex cursor-pointer items-center gap-3 border-b border-gray-100 px-4 py-2.5 last:border-0 hover:bg-gray-50"
          >
            <input
              type="checkbox"
              checked={selected.includes(u.id)}
              onChange={() => onToggle(u.id)}
              className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
            <span className="text-sm text-gray-800">
              {u.apellidos}, {u.nombre}
            </span>
            <span className="ml-auto text-xs text-gray-400">{u.legajo}</span>
          </label>
        ))}
      </div>

      <div className="flex gap-3">
        <button
          type="button"
          onClick={onPrev}
          className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          Anterior
        </button>
        <button
          type="button"
          onClick={onNext}
          disabled={selected.length === 0}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-40"
        >
          Siguiente ({selected.length})
        </button>
      </div>
    </div>
  );
}

// ── Paso 3: Configuración de la asignación ───────────────────────────────────

interface ConfigForm {
  role_id: string;
  comisiones: string;
  desde: string;
  hasta: string;
}

function PasoConfiguracion({
  value,
  onChange,
  onSubmit,
  onPrev,
  isPending,
  error,
}: {
  value: ConfigForm;
  onChange: (v: ConfigForm) => void;
  onSubmit: () => void;
  onPrev: () => void;
  isPending: boolean;
  error: boolean;
}) {
  const { data: roles = [], isLoading: loadingRoles } = useRoles();

  const canSubmit =
    value.role_id && value.desde && !isPending;

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Paso 3: Configuración</h2>

      <div>
        <label className="block text-sm font-medium text-gray-700">Rol</label>
        <select
          value={value.role_id}
          onChange={(e) => onChange({ ...value, role_id: e.target.value })}
          disabled={loadingRoles}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:bg-gray-50"
        >
          <option value="">Seleccioná un rol…</option>
          {roles.map((r) => (
            <option key={r.id} value={r.id}>{r.nombre}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">
          Comisiones <span className="text-gray-400">(separadas por coma, opcional)</span>
        </label>
        <input
          type="text"
          placeholder="A, B, C"
          value={value.comisiones}
          onChange={(e) => onChange({ ...value, comisiones: e.target.value })}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Vigencia desde *</label>
          <input
            type="date"
            value={value.desde}
            onChange={(e) => onChange({ ...value, desde: e.target.value })}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Vigencia hasta <span className="text-gray-400">(opcional)</span>
          </label>
          <input
            type="date"
            value={value.hasta}
            onChange={(e) => onChange({ ...value, hasta: e.target.value })}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
      </div>

      {error && (
        <p className="text-sm text-red-600">
          Error al crear asignaciones. Revisá los datos e intentá de nuevo.
        </p>
      )}

      <div className="flex gap-3">
        <button
          type="button"
          onClick={onPrev}
          disabled={isPending}
          className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40"
        >
          Anterior
        </button>
        <button
          type="button"
          onClick={onSubmit}
          disabled={!canSubmit}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-40"
        >
          {isPending ? 'Asignando…' : 'Asignar docentes'}
        </button>
      </div>
    </div>
  );
}

// ── Resultado ────────────────────────────────────────────────────────────────

function PasoResultado({
  result,
  onReset,
}: {
  result: AsignacionMasivaResult;
  onReset: () => void;
}) {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Resultado</h2>

      <div className="rounded-md bg-green-50 px-4 py-3 text-sm text-green-800">
        ✓ {result.creadas} asignación{result.creadas !== 1 ? 'es' : ''} creada{result.creadas !== 1 ? 's' : ''}
      </div>

      {result.rechazadas.length > 0 && (
        <div className="rounded-md bg-red-50 px-4 py-3">
          <p className="text-sm font-medium text-red-800">
            {result.rechazadas.length} rechazada{result.rechazadas.length !== 1 ? 's' : ''}:
          </p>
          <ul className="mt-1 list-inside list-disc space-y-0.5 text-sm text-red-700">
            {result.rechazadas.map((r, i) => (
              <li key={i}>{r.motivo}</li>
            ))}
          </ul>
        </div>
      )}

      {result.omitidas.length > 0 && (
        <div className="rounded-md bg-yellow-50 px-4 py-3">
          <p className="text-sm font-medium text-yellow-800">
            {result.omitidas.length} omitida{result.omitidas.length !== 1 ? 's' : ''} (ya existían):
          </p>
          <ul className="mt-1 list-inside list-disc space-y-0.5 text-sm text-yellow-700">
            {result.omitidas.map((o, i) => (
              <li key={i}>{o.motivo}</li>
            ))}
          </ul>
        </div>
      )}

      <button
        type="button"
        onClick={onReset}
        className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
      >
        Nueva asignación
      </button>
    </div>
  );
}

// ── Formulario principal ─────────────────────────────────────────────────────

export function AsignacionMasivaForm() {
  const [step, setStep] = useState(1);
  const [contexto, setContexto] = useState<ContextoForm>({
    materia_id: '',
    carrera_id: '',
    cohorte_id: '',
  });
  const [usuariosSeleccionados, setUsuariosSeleccionados] = useState<string[]>([]);
  const [config, setConfig] = useState<ConfigForm>({
    role_id: '',
    comisiones: '',
    desde: '',
    hasta: '',
  });
  const [result, setResult] = useState<AsignacionMasivaResult | null>(null);

  const mutation = useAsignacionMasiva();

  const toggleUsuario = (id: string) => {
    setUsuariosSeleccionados((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  };

  const handleSubmit = () => {
    const comisiones = config.comisiones
      ? config.comisiones.split(',').map((c) => c.trim()).filter(Boolean)
      : [];

    mutation.mutate(
      {
        usuario_ids: usuariosSeleccionados,
        role_id: config.role_id,
        materia_id: contexto.materia_id || undefined,
        carrera_id: contexto.carrera_id || undefined,
        cohorte_id: contexto.cohorte_id || undefined,
        comisiones,
        desde: config.desde,
        hasta: config.hasta || undefined,
      },
      {
        onSuccess: (res) => {
          setResult(res);
          setStep(4);
        },
      },
    );
  };

  const handleReset = () => {
    setStep(1);
    setContexto({ materia_id: '', carrera_id: '', cohorte_id: '' });
    setUsuariosSeleccionados([]);
    setConfig({ role_id: '', comisiones: '', desde: '', hasta: '' });
    setResult(null);
    mutation.reset();
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      {/* Indicador de pasos */}
      {step < 4 && (
        <div className="mb-6 flex items-center gap-2">
          {[1, 2, 3].map((s) => (
            <div key={s} className="flex items-center gap-2">
              <div
                className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-medium ${
                  s === step
                    ? 'bg-indigo-600 text-white'
                    : s < step
                    ? 'bg-indigo-100 text-indigo-700'
                    : 'bg-gray-100 text-gray-400'
                }`}
              >
                {s}
              </div>
              {s < 3 && <div className="h-px w-6 bg-gray-200" />}
            </div>
          ))}
        </div>
      )}

      {step === 1 && (
        <PasoContexto
          value={contexto}
          onChange={setContexto}
          onNext={() => setStep(2)}
        />
      )}
      {step === 2 && (
        <PasoDocentes
          selected={usuariosSeleccionados}
          onToggle={toggleUsuario}
          onNext={() => setStep(3)}
          onPrev={() => setStep(1)}
        />
      )}
      {step === 3 && (
        <PasoConfiguracion
          value={config}
          onChange={setConfig}
          onSubmit={handleSubmit}
          onPrev={() => setStep(2)}
          isPending={mutation.isPending}
          error={mutation.isError}
        />
      )}
      {step === 4 && result && (
        <PasoResultado result={result} onReset={handleReset} />
      )}
    </div>
  );
}
