import type { RolLiquidacion, GrupoPlus } from '@/features/finanzas/types';

export const grillaKeys = {
  base: {
    all: ['grilla', 'salarios-base'] as const,
    list: (rol?: RolLiquidacion) => ['grilla', 'salarios-base', rol] as const,
  },
  plus: {
    all: ['grilla', 'salarios-plus'] as const,
    list: (grupo?: GrupoPlus) => ['grilla', 'salarios-plus', grupo] as const,
  },
};
