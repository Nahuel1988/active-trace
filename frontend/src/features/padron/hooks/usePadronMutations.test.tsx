import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

const { mockPreviewPadron, mockCommitPadron } = vi.hoisted(() => ({
  mockPreviewPadron: vi.fn(),
  mockCommitPadron: vi.fn(),
}));

vi.mock('@/features/padron/services/padronApi', () => ({
  previewPadron: mockPreviewPadron,
  commitPadron: mockCommitPadron,
}));

import { usePadronPreview, usePadronCommit } from './usePadronMutations';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe('usePadronPreview', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns preview data on success', async () => {
    const preview = { import_id: 'i1', alumnos: [], total_detectados: 0, errores: [] };
    mockPreviewPadron.mockResolvedValue(preview);

    const { result } = renderHook(() => usePadronPreview(), { wrapper: createWrapper() });
    const file = new File(['test'], 'test.xlsx');

    result.current.mutate({ materia_id: 'm1', file });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(preview);
  });

  it('propagates error on format error', async () => {
    mockPreviewPadron.mockRejectedValue(new Error('Invalid format'));

    const { result } = renderHook(() => usePadronPreview(), { wrapper: createWrapper() });
    const file = new File(['test'], 'test.xlsx');

    result.current.mutate({ materia_id: 'm1', file });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('usePadronCommit', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls commit and returns result', async () => {
    const commitResult = { total_importados: 5, total_reemplazados: 2 };
    mockCommitPadron.mockResolvedValue(commitResult);

    const { result } = renderHook(() => usePadronCommit(), { wrapper: createWrapper() });

    result.current.mutate({ materia_id: 'm1', import_id: 'i1' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(commitResult);
    expect(mockCommitPadron).toHaveBeenCalledWith('m1', 'i1');
  });

  it('handles error on commit failure', async () => {
    mockCommitPadron.mockRejectedValue(new Error('Commit failed'));

    const { result } = renderHook(() => usePadronCommit(), { wrapper: createWrapper() });

    result.current.mutate({ materia_id: 'm1', import_id: 'i1' });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
