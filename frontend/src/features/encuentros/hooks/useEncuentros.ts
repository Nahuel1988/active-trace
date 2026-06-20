import { useQuery } from '@tanstack/react-query';
import { encuentrosKeys } from './encuentrosKeys';
import * as encuentrosApi from '../services/encuentrosApi';
import type { InstanciaFilters } from '../types';

export function useSlots(materia_id?: string) {
  return useQuery({
    queryKey: encuentrosKeys.slots.list({ materia_id }),
    queryFn: () => encuentrosApi.fetchSlots(materia_id),
  });
}

export function useSlot(id: string) {
  return useQuery({
    queryKey: encuentrosKeys.slots.detail(id),
    queryFn: () => encuentrosApi.fetchSlot(id),
    enabled: !!id,
  });
}

export function useInstancias(filters?: InstanciaFilters) {
  return useQuery({
    queryKey: encuentrosKeys.instancias.list(filters as Record<string, unknown> | undefined),
    queryFn: () => encuentrosApi.fetchInstancias(filters),
  });
}
