import { useState } from 'react';
import type { InstanciaEncuentro, EstadoInstancia } from '../types';

interface InstanciaRowProps {
  instancia: InstanciaEncuentro;
  onSave: (instancia_id: string, data: {
    estado?: EstadoInstancia;
    meet_url?: string | null;
    video_url?: string | null;
    comentario?: string | null;
  }) => void;
  isSaving?: boolean;
}

const ESTADOS: { value: EstadoInstancia; label: string }[] = [
  { value: 'programado', label: 'Programado' },
  { value: 'realizado', label: 'Realizado' },
  { value: 'cancelado', label: 'Cancelado' },
];

export function InstanciaRow({ instancia, onSave, isSaving }: InstanciaRowProps) {
  const [estado, setEstado] = useState<EstadoInstancia>(instancia.estado);
  const [meetUrl, setMeetUrl] = useState(instancia.meet_url ?? '');
  const [videoUrl, setVideoUrl] = useState(instancia.video_url ?? '');
  const [comentario, setComentario] = useState(instancia.comentario ?? '');

  const hasChanges =
    estado !== instancia.estado ||
    meetUrl !== (instancia.meet_url ?? '') ||
    videoUrl !== (instancia.video_url ?? '') ||
    comentario !== (instancia.comentario ?? '');

  const handleSave = () => {
    onSave(instancia.id, {
      estado,
      meet_url: meetUrl || null,
      video_url: videoUrl || null,
      comentario: comentario || null,
    });
  };

  return (
    <tr className="hover:bg-gray-50">
      <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-900">
        {new Date(instancia.fecha).toLocaleDateString('es-AR')}
      </td>
      <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-600">
        {instancia.hora}
      </td>
      <td className="px-4 py-3">
        <select
          value={estado}
          onChange={(e) => setEstado(e.target.value as EstadoInstancia)}
          className="block w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          {ESTADOS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </td>
      <td className="px-4 py-3">
        <input
          type="text"
          value={meetUrl}
          onChange={(e) => setMeetUrl(e.target.value)}
          placeholder="https://meet..."
          className="block w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
      </td>
      <td className="px-4 py-3">
        <input
          type="text"
          value={videoUrl}
          onChange={(e) => setVideoUrl(e.target.value)}
          placeholder="https://..."
          className="block w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
      </td>
      <td className="px-4 py-3">
        <textarea
          value={comentario}
          onChange={(e) => setComentario(e.target.value)}
          rows={1}
          placeholder="Comentario..."
          className="block w-full rounded-md border border-gray-300 px-2 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
      </td>
      <td className="whitespace-nowrap px-4 py-3">
        <button
          type="button"
          onClick={handleSave}
          disabled={!hasChanges || isSaving}
          className="rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isSaving ? 'Guardando...' : 'Guardar'}
        </button>
      </td>
    </tr>
  );
}
