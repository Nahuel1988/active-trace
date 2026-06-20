import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';

vi.mock('@/features/finanzas/hooks/useGrilla', () => ({
  useSalariosBase: () => ({ data: [], isLoading: false }),
  useSalariosPlus: () => ({ data: [], isLoading: false }),
}));

vi.mock('@/features/finanzas/hooks/useGrillaMutations', () => ({
  useCrearSalarioBase: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useActualizarSalarioBase: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useEliminarSalarioBase: () => ({ mutate: vi.fn() }),
  useCrearSalarioPlus: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useActualizarSalarioPlus: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useEliminarSalarioPlus: () => ({ mutate: vi.fn() }),
}));

import { GrillaSalarialPage } from './GrillaSalarialPage';

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe('GrillaSalarialPage', () => {
  it('renderiza la sección de Salario Base', () => {
    render(<GrillaSalarialPage />, { wrapper });
    expect(screen.getByText('Salario Base')).toBeInTheDocument();
  });

  it('renderiza la sección de Salario Plus', () => {
    render(<GrillaSalarialPage />, { wrapper });
    expect(screen.getByText('Salario Plus')).toBeInTheDocument();
  });

  it('muestra botón de alta en cada sección', () => {
    render(<GrillaSalarialPage />, { wrapper });
    const botonesNuevo = screen.getAllByRole('button', { name: /nuevo/i });
    expect(botonesNuevo.length).toBeGreaterThanOrEqual(2);
  });
});
