// ── UsuarioDetail ──────────────────────────────────────────────────────────
// Read-only detail view for a single Usuario, including PII fields.
// SECURITY (D-04): This component is the ONLY authorised place to display PII.
// Do NOT console.log any field. Do NOT pass PII as props to child components.

import type { UsuarioDetalle } from '@/features/admin/types';

interface UsuarioDetailProps {
  usuario: UsuarioDetalle;
}

function DetailRow({ label, value }: { label: string; value: string | null | boolean }) {
  const display =
    value === null || value === undefined
      ? '—'
      : typeof value === 'boolean'
      ? value ? 'Sí' : 'No'
      : value;

  return (
    <div className="sm:col-span-1">
      <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide">
        {label}
      </dt>
      <dd className="mt-1 text-sm text-gray-900">{display}</dd>
    </div>
  );
}

function PiiRow({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="sm:col-span-1">
      <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide">
        {label}
      </dt>
      <dd className="mt-1">
        <input
          type="text"
          readOnly
          value={value ?? '—'}
          className="block w-full rounded-md border border-gray-200 bg-gray-50 px-3 py-1.5 text-sm text-gray-900 cursor-default focus:outline-none"
        />
      </dd>
    </div>
  );
}

export function UsuarioDetail({ usuario }: UsuarioDetailProps) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-base font-semibold text-gray-900 mb-4">
          Datos generales
        </h3>
        <dl className="grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2">
          <DetailRow label="Legajo" value={usuario.legajo} />
          <DetailRow label="Regional" value={usuario.regional} />
          <DetailRow label="Nombre" value={usuario.nombre} />
          <DetailRow label="Apellidos" value={usuario.apellidos} />
          <div className="sm:col-span-2">
            <DetailRow label="Email" value={usuario.email} />
          </div>
          <DetailRow label="Facturador" value={usuario.facturador} />
          <DetailRow label="Estado" value={usuario.is_active ? 'Activo' : 'Baja'} />
          <DetailRow label="Alta" value={new Date(usuario.created_at).toLocaleDateString('es-AR')} />
          <DetailRow label="Última modificación" value={new Date(usuario.updated_at).toLocaleDateString('es-AR')} />
        </dl>
      </div>

      <hr className="border-gray-200" />

      <div>
        <h3 className="text-base font-semibold text-gray-900 mb-1">
          Datos sensibles
        </h3>
        <p className="text-xs text-gray-500 mb-4">
          Esta información es confidencial y sólo visible en esta pantalla.
        </p>
        <dl className="grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2">
          <PiiRow label="DNI" value={usuario.dni} />
          <PiiRow label="CUIL" value={usuario.cuil} />
          <PiiRow label="CBU" value={usuario.cbu} />
          <PiiRow label="Alias CBU" value={usuario.alias_cbu} />
        </dl>
      </div>
    </div>
  );
}
