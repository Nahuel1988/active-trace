import { useMutation, useQueryClient } from '@tanstack/react-query';
import { encuentrosKeys } from './encuentrosKeys';
import * as encuentrosApi from '../services/encuentrosApi';
import type { SlotCreateRequest, InstanciaEditRequest } from '../types';

export function useCrearSlot() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SlotCreateRequest) => encuentrosApi.crearSlot(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: encuentrosKeys.slots.lists() });
    },
  });
}

export function useEliminarSlot() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (slot_id: string) => encuentrosApi.eliminarSlot(slot_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: encuentrosKeys.slots.lists() });
    },
  });
}

export function useEditarInstancia() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      instancia_id,
      data,
    }: {
      instancia_id: string;
      data: InstanciaEditRequest;
    }) => encuentrosApi.editarInstancia(instancia_id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: encuentrosKeys.all });
    },
  });
}
