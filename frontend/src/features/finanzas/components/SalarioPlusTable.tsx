import type { SalarioPlus, GrupoPlus } from '@/features/finanzas/types';

const GRUPOS: GrupoPlus[] = ['PROG', 'BD', 'ARQ', 'MAT', 'MET'];

interface Props {
  items: SalarioPlus[];
  grupoFilter?: GrupoPlus;
  onGrupoFilter: (grupo?: GrupoPlus) => void;
  onEditar: (item: SalarioPlus) => void;
  onEliminar: (id: string) => void;
}

export function SalarioPlusTable({ items, grupoFilter, onGrupoFilter, onEditar, onEliminar }: Props) {
  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <select
          value={grupoFilter ?? ''}
          onChange={(e) => onGrupoFilter((e.target.value as GrupoPlus) || undefined)}
          className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
          aria-label="Filtrar por grupo"
        >
          <option value="">Todos los grupos</option>
          {GRUPOS.map((g) => <option key={g} value={g}>{g}</option>)}
        </select>
      </div>
      {items.length === 0 ? (
        <p className="text-center text-gray-400 py-8">Sin plus configurados</p>
      ) : (
        <table className="w-full text-sm border border-gray-200 rounded-lg overflow-hidden">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left">Grupo</th>
              <th className="px-4 py-2 text-left">Rol</th>
              <th className="px-4 py-2 text-left">Descripción</th>
              <th className="px-4 py-2 text-right">Monto</th>
              <th className="px-4 py-2 text-left">Desde</th>
              <th className="px-4 py-2 text-left">Hasta</th>
              <th className="px-4 py-2" />
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="border-t border-gray-100">
                <td className="px-4 py-2">{item.grupo}</td>
                <td className="px-4 py-2">{item.rol}</td>
                <td className="px-4 py-2">{item.descripcion}</td>
                <td className="px-4 py-2 text-right">${parseFloat(item.monto).toLocaleString('es-AR', { minimumFractionDigits: 2 })}</td>
                <td className="px-4 py-2">{item.desde}</td>
                <td className="px-4 py-2">{item.hasta ?? '—'}</td>
                <td className="px-4 py-2 flex gap-2">
                  <button onClick={() => onEditar(item)} className="text-xs text-blue-600 hover:underline">Editar</button>
                  <button onClick={() => onEliminar(item.id)} className="text-xs text-red-600 hover:underline">Eliminar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
