import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { MemoryRouter, useSearchParams } from 'react-router-dom';
import type { ReactNode } from 'react';
import { ComisionProvider } from './ComisionContext';
import { useComisionContext } from './useComisionContext';

function createWrapper(initialEntries = ['/']) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <MemoryRouter initialEntries={initialEntries}>
        <ComisionProvider>{children}</ComisionProvider>
      </MemoryRouter>
    );
  };
}

describe('useComisionContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns empty selection when no query params', () => {
    const { result } = renderHook(() => useComisionContext(), {
      wrapper: createWrapper(),
    });

    expect(result.current.materia_id).toBe('');
    expect(result.current.cohorte_id).toBe('');
  });

  it('reads materia and cohorte from URL query params', () => {
    const { result } = renderHook(() => useComisionContext(), {
      wrapper: createWrapper(['/?materia=m1&cohorte=c1']),
    });

    expect(result.current.materia_id).toBe('m1');
    expect(result.current.cohorte_id).toBe('c1');
  });

  it('setComision updates URL query params', () => {
    const { result } = renderHook(() => useComisionContext(), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.setComision('m1', 'c1');
    });

    expect(result.current.materia_id).toBe('m1');
    expect(result.current.cohorte_id).toBe('c1');
  });

  it('persists selection on url change', () => {
    const { result, rerender } = renderHook(() => useComisionContext(), {
      wrapper: createWrapper(['/?materia=m1&cohorte=c1']),
    });

    expect(result.current.materia_id).toBe('m1');
    expect(result.current.cohorte_id).toBe('c1');
  });

  it('clears cohorte when materia changes', () => {
    const { result } = renderHook(() => useComisionContext(), {
      wrapper: createWrapper(['/?materia=m1&cohorte=c1']),
    });

    act(() => {
      result.current.setComision('m2', '');
    });

    expect(result.current.materia_id).toBe('m2');
    expect(result.current.cohorte_id).toBe('');
  });
});
