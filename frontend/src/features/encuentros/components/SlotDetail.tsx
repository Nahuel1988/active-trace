import { useState } from 'react';
import type { SlotEncuentro, EstadoInstancia } from '../types';
import { InstanciaRow } from './InstanciaRow';

interface SlotDetailProps {
  slot: SlotEncuentro;
  onSaveInstancia: (
    instancia_id: string,
    data: {
      estado?: EstadoInstancia;
      meet_url?: string | null;
      video_url?: string | null;
      comentario?: string | null;
    },
  ) => void;
  isSaving?: boolean;
}

const DIAS: Record<string, string> = {
  lunes: 'Lunes',
  martes: 'Martes',
  miércoles: 'Miércoles',
  jueves: 'Jueves',
  viernes: 'Viernes',
  sábado: 'Sábado',
  domingo: 'Domingo',
};

export function SlotDetail({ slot, onSaveInstancia, isSaving }: SlotDetailProps) {
  const [copied, setCopied] = useState(false);

  const handleCopyHTML = async () => {
    try {
      const { exportarHTML } = await import('../services/encuentrosApi');
      const html = await exportarHTML(slot.id);
      await navigator.clipboard.writeText(html);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Silently fail — user can retry
    }
  };

  return (
    <div className="space-y-6">
      {/* Slot metadata card */}
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">{slot.titulo}</h2>
            <p className="mt-1 text-sm text-gray-500">
              Materia: {slot.materia_id.slice(0, 8)}...
            </p>
          </div>
          <button
            type="button"
            onClick={handleCopyHTML}
            className="rounded-md bg-green-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-green-500"
          >
            {copied ? 'Copiado' : 'Copiar HTML'}
          </button>
        </div>

        <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div>
            <dt className="text-xs font-medium text-gray-500">Día</dt>
            <dd className="mt-1 text-sm text-gray-900">
              {DIAS[slot.dia_semana] ?? slot.dia_semana}
            </dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Hora</dt>
            <dd className="mt-1 text-sm text-gray-900">{slot.hora}</dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Tipo</dt>
            <dd className="mt-1 text-sm text-gray-900">
              <span
                className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${
                  slot.modo === 'recurrente'
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-purple-100 text-purple-700'
                }`}
              >
                {slot.modo === 'recurrente' ? 'Recurrente' : 'Único'}
              </span>
            </dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-gray-500">Inicio</dt>
            <dd className="mt-1 text-sm text-gray-900">
              {new Date(slot.fecha_inicio).toLocaleDateString('es-AR')}
            </dd>
          </div>
          {slot.cant_semanas && (
            <div>
              <dt className="text-xs font-medium text-gray-500">Semanas</dt>
              <dd className="mt-1 text-sm text-gray-900">{slot.cant_semanas}</dd>
            </div>
          )}
          {slot.fecha_unica && (
            <div>
              <dt className="text-xs font-medium text-gray-500">Fecha única</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {new Date(slot.fecha_unica).toLocaleDateString('es-AR')}
              </dd>
            </div>
          )}
          <div>
            <dt className="text-xs font-medium text-gray-500">Vigencia</dt>
            <dd className="mt-1 text-sm text-gray-900">
              {new Date(slot.vig_desde).toLocaleDateString('es-AR')}
              {slot.vig_hasta
                ? ` — ${new Date(slot.vig_hasta).toLocaleDateString('es-AR')}`
                : ' — ∞'}
            </dd>
          </div>
        </dl>
      </div>

      {/* Instancias table */}
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Fecha</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Hora</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Estado</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Meet URL</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Video URL</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Comentario</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {(slot.instancias ?? []).length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-sm text-gray-500">
                  No hay instancias generadas
                </td>
              </tr>
            ) : (
              slot.instancias!.map((instancia) => (
                <InstanciaRow
                  key={instancia.id}
                  instancia={instancia}
                  onSave={onSaveInstancia}
                  isSaving={isSaving}
                />
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
