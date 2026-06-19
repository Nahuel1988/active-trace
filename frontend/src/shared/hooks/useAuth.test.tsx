// ── Tests: shared/hooks/useAuth ──────────────────────────────────────────────
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';

// ── Mock api module — must be before static imports ─────────────────────────
const { mockApiPost } = vi.hoisted(() => ({
  mockApiPost: vi.fn(),
}));

vi.mock('@/shared/services/api', () => ({
  api: {
    post: mockApiPost,
    get: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
    defaults: { baseURL: '', withCredentials: true },
  },
  setAccessToken: vi.fn(),
  setOnSessionExpired: vi.fn(),
  getAccessToken: vi.fn(),
  ForbiddenError: class ForbiddenError extends Error {
    constructor(message?: string) {
      super(message ?? 'Forbidden');
      this.name = 'ForbiddenError';
    }
  },
}));

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApiPost.mockRejectedValue(new Error('no session'));
  });

  // ── 2.7: useAuth fuera del provider → error ──────────────────────────────
  it('throws error when used outside AuthProvider', async () => {
    const { useAuth } = await import('./useAuth');

    function TestComponent() {
      useAuth();
      return <div>should not render</div>;
    }

    // Suppress console.error from React error boundary
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => render(<TestComponent />)).toThrow(
      'useAuth must be used within an AuthProvider',
    );

    consoleSpy.mockRestore();
  });

  // ── 2.7: useAuth dentro del provider → ok ────────────────────────────────
  it('works inside AuthProvider', async () => {
    const { AuthProvider } = await import('@/shared/context/AuthContext');
    const { useAuth } = await import('./useAuth');

    function TestComponent() {
      const { isAuthenticated } = useAuth();
      return (
        <span data-testid="auth-state">{String(isAuthenticated)}</span>
      );
    }

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>,
    );

    // Wait for refresh effect to settle (isLoading → false)
    await waitFor(() => {
      expect(screen.getByTestId('auth-state').textContent).toBe('false');
    });
  });
});
