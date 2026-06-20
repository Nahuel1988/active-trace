import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';

vi.mock('@/shared/comision/useComisionContext', () => ({
  useComisionContext: () => ({ materia_id: '', cohorte_id: '', setComision: vi.fn() }),
}));

vi.mock('@/features/finanzas/hooks/useLiquidaciones', () => ({
  useLiquidaciones: () => ({ data: undefined, isLoading: false }),
}));

vi.mock('@/features/finanzas/hooks/useLiquidacionMutations', () => ({
  useCerrarLiquidacion: () => ({ mutate: vi.fn(), isPending: false }),
  useCalcularPeriodo: () => ({ mutate: vi.fn(), isPending: false }),
}));

import { LiquidacionesPage } from './LiquidacionesPage';

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={client}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe('LiquidacionesPage', () => {
  it('muestra estado pidiendo seleccionar período cuando no hay cohorte ni período', () => {
    render(<LiquidacionesPage />, { wrapper });
    expect(screen.getByText(/seleccioná una comisión y un período/i)).toBeInTheDocument();
  });

  it('no muestra acciones de mutación en modo solo-lectura', () => {
    render(<LiquidacionesPage canCerrar={false} canCalcular={false} />, { wrapper });
    expect(screen.queryByRole('button', { name: /calcular/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /cerrar/i })).not.toBeInTheDocument();
  });

  it('muestra botón de calcular cuando canCalcular es true', () => {
    render(<LiquidacionesPage canCalcular />, { wrapper });
    expect(screen.getByRole('button', { name: /calcular período/i })).toBeInTheDocument();
  });
});
