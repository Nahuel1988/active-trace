import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  crearSalarioBase,
  actualizarSalarioBase,
  eliminarSalarioBase,
  crearSalarioPlus,
  actualizarSalarioPlus,
  eliminarSalarioPlus,
} from '@/features/finanzas/services/grillaApi';
import { grillaKeys } from '@/features/finanzas/services/grillaKeys';
import type { SalarioBaseFormData, SalarioPlusFormData } from '@/features/finanzas/types';

export function useCrearSalarioBase() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: SalarioBaseFormData) => crearSalarioBase(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: grillaKeys.base.all }),
  });
}

export function useActualizarSalarioBase() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Pick<SalarioBaseFormData, 'monto' | 'hasta'>> }) =>
      actualizarSalarioBase(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: grillaKeys.base.all }),
  });
}

export function useEliminarSalarioBase() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => eliminarSalarioBase(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: grillaKeys.base.all }),
  });
}

export function useCrearSalarioPlus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: SalarioPlusFormData) => crearSalarioPlus(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: grillaKeys.plus.all }),
  });
}

export function useActualizarSalarioPlus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Pick<SalarioPlusFormData, 'descripcion' | 'monto' | 'hasta'>> }) =>
      actualizarSalarioPlus(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: grillaKeys.plus.all }),
  });
}

export function useEliminarSalarioPlus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => eliminarSalarioPlus(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: grillaKeys.plus.all }),
  });
}
