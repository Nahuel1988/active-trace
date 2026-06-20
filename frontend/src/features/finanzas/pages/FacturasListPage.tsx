import { useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/shared/services/api';
import { useFacturas } from '@/features/finanzas/hooks/useFacturas';
import { useCrearFactura } from '@/features/finanzas/hooks/useFacturaMutations';
import { FacturaTable } from '@/features/finanzas/components/FacturaTable';
import { FacturaFormDialog } from '@/features/finanzas/components/FacturaFormDialog';
import type { EstadoFactura, FacturaFilters, FacturaFormData } from '@/features/finanzas/types';

interface Facturador {
  id: string;
  nombre: string;
  apellidos: string;
}

function useFacturadores() {
  return useQuery<Facturador[]>({
    queryKey: ['usuarios', 'facturadores'],
    queryFn: () =>
      api.get('/api/v1/admin/usuarios', { params: { facturador: true } }).then((r) => r.data),
    staleTime: 5 * 60_000,
  });
}

export function FacturasListPage() {
  const [filters, setFilters] = useState<FacturaFilters>({});
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const { data: facturas = [], isLoading } = useFacturas(filters);
  const { data: facturadores = [] } = useFacturadores();
  const { mutate: crearFactura, isPending: isCreating } = useCrearFactura();

  const handlePeriodoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilters((prev) => ({ ...prev, periodo: e.target.value || undefined }));
  };

  const handleEstadoChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value as EstadoFactura | '';
    setFilters((prev) => ({ ...prev, estado: val || undefined }));
  };

  const handleOpenDialog = () => {
    setFormError(null);
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setFormError(null);
  };

  const handleSubmit = useCallback(
    (data: FacturaFormData) => {
      setFormError(null);
      crearFactura(data, {
        onSuccess: () => {
          setDialogOpen(false);
        },
        onError: (err: unknown) => {
          const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
          const status = axiosErr.response?.status;
          const detail = axiosErr.response?.data?.detail;
          if (status === 422) {
            setFormError(detail ?? 'Error de validación. Revisá los campos ingresados.');
          } else {
            setFormError(detail ?? 'Error al crear la factura.');
          }
        },
      });
    },
    [crearFactura],
  );

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Facturas</h1>
        <button
          type="button"
          onClick={handleOpenDialog}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          Nueva factura
        </button>
      </div>

      <div className="mb-4 flex flex-wrap gap-3">
        <input
          type="text"
          value={filters.periodo ?? ''}
          onChange={handlePeriodoChange}
          placeholder="Período (ej. 2025-06)"
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          aria-label="Filtrar por período"
        />
        <select
          value={filters.estado ?? ''}
          onChange={handleEstadoChange}
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          aria-label="Filtrar por estado"
        >
          <option value="">Todos los estados</option>
          <option value="Pendiente">Pendiente</option>
          <option value="Abonada">Abonada</option>
        </select>
      </div>

      {isLoading ? (
        <p className="py-8 text-center text-gray-400">Cargando facturas...</p>
      ) : (
        <FacturaTable facturas={facturas} canAbonar />
      )}

      <FacturaFormDialog
        open={dialogOpen}
        onClose={handleCloseDialog}
        onSubmit={handleSubmit}
        isPending={isCreating}
        error={formError}
        facturadores={facturadores}
      />
    </div>
  );
}
