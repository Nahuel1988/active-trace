import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  crearFactura,
  actualizarFactura,
  abonarFactura,
} from '@/features/finanzas/services/facturasApi';
import { facturasKeys } from '@/features/finanzas/services/facturasKeys';
import type { FacturaFormData } from '@/features/finanzas/types';

export function useCrearFactura() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: FacturaFormData) => crearFactura(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: facturasKeys.all });
    },
  });
}

export function useActualizarFactura() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
      data: Partial<Pick<FacturaFormData, 'detalle' | 'referencia_archivo' | 'tamano_kb'>>;
    }) => actualizarFactura(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: facturasKeys.all });
    },
  });
}

export function useAbonarFactura() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => abonarFactura(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: facturasKeys.all });
    },
  });
}
