// ── Tests: shared/context/AuthContext ─────────────────────────────────────────
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useAuth } from '@/shared/hooks/useAuth';

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

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApiPost.mockRejectedValue(new Error('no session'));
  });

  // ── 2.2: Estado inicial no autenticado ──────────────────────────────────
  it('provides default unauthenticated state', async () => {
    const { AuthProvider } = await import('./AuthContext');

    function TestComponent() {
      const auth = useAuth();
      return (
        <div>
          <span data-testid="isAuthenticated">
            {String(auth.isAuthenticated)}
          </span>
          <span data-testid="pendingTwoFactor">
            {String(auth.pendingTwoFactor)}
          </span>
          <span data-testid="user">{JSON.stringify(auth.user)}</span>
          <span data-testid="token">{auth.accessToken}</span>
        </div>
      );
    }

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>,
    );

    // Initially isLoading=true, so isAuthenticated is false
    await waitFor(() => {
      expect(screen.getByTestId('isAuthenticated').textContent).toBe('false');
    });
    expect(screen.getByTestId('pendingTwoFactor').textContent).toBe('false');
    expect(screen.getByTestId('user').textContent).toBe('null');
    expect(screen.getByTestId('token').textContent).toBe('');
  });

  // ── 2.2: setSession actualiza estado ────────────────────────────────────
  it('setSession updates state correctly', async () => {
    const user = userEvent.setup();
    const { AuthProvider } = await import('./AuthContext');

    const mockUser = {
      user_id: 'u1',
      tenant_id: 't1',
      roles: ['admin'] as string[],
      permissions: ['users:read', 'users:write'] as string[],
    };

    function TestComponent() {
      const auth = useAuth();
      return (
        <div>
          <button
            data-testid="login-btn"
            onClick={() => auth.setSession(mockUser, 'token-123')}
          >
            Login
          </button>
          <span data-testid="isAuthenticated">
            {String(auth.isAuthenticated)}
          </span>
          <span data-testid="user-id">{auth.user?.user_id ?? 'none'}</span>
          <span data-testid="token-value">{auth.accessToken ?? 'none'}</span>
        </div>
      );
    }

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>,
    );

    // Wait for refresh effect to settle (isLoading → false)
    await waitFor(() => {
      expect(screen.getByTestId('isAuthenticated').textContent).toBe('false');
    });

    await user.click(screen.getByTestId('login-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('isAuthenticated').textContent).toBe('true');
    });
    expect(screen.getByTestId('user-id').textContent).toBe('u1');
    expect(screen.getByTestId('token-value').textContent).toBe('token-123');
  });

  // ── 2.2: clearSession resetea estado ─────────────────────────────────────
  it('clearSession resets state to unauthenticated', async () => {
    const user = userEvent.setup();
    const { AuthProvider } = await import('./AuthContext');

    function TestComponent() {
      const auth = useAuth();
      return (
        <div>
          <button
            data-testid="login-btn"
            onClick={() =>
              auth.setSession(
                {
                  user_id: 'u1',
                  tenant_id: 't1',
                  roles: [],
                  permissions: [],
                },
                'token-123',
              )
            }
          >
            Login
          </button>
          <button data-testid="logout-btn" onClick={() => auth.clearSession()}>
            Logout
          </button>
          <span data-testid="isAuthenticated">
            {String(auth.isAuthenticated)}
          </span>
          <span data-testid="user-state">{JSON.stringify(auth.user)}</span>
        </div>
      );
    }

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>,
    );

    // Wait for initial load, then login
    await waitFor(() => {
      expect(screen.getByTestId('isAuthenticated').textContent).toBe('false');
    });

    await user.click(screen.getByTestId('login-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('isAuthenticated').textContent).toBe('true');
    });

    // Logout
    await user.click(screen.getByTestId('logout-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('isAuthenticated').textContent).toBe('false');
    });
    expect(screen.getByTestId('user-state').textContent).toBe('null');
  });

  // ── isLoading: true on mount, false after refresh completes ──────────────
  it('isLoading is true on mount, becomes false after refresh completes', async () => {
    const { AuthProvider } = await import('./AuthContext');

    function TestComponent() {
      const { isLoading } = useAuth();
      return <span data-testid="loading">{String(isLoading)}</span>;
    }

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>,
    );

    // Initially isLoading is true
    expect(screen.getByTestId('loading').textContent).toBe('true');

    // After the refresh effect rejects, isLoading becomes false
    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('false');
    });
  });

  // ── setPendingTwoFactor ─────────────────────────────────────────────────
  it('setPendingTwoFactor updates pendingTwoFactor state', async () => {
    const user = userEvent.setup();
    const { AuthProvider } = await import('./AuthContext');

    function TestComponent() {
      const auth = useAuth();
      return (
        <div>
          <button
            data-testid="2fa-btn"
            onClick={() => auth.setPendingTwoFactor(true)}
          >
            Enable 2FA
          </button>
          <span data-testid="isAuthenticated">
            {String(auth.isAuthenticated)}
          </span>
          <span data-testid="pending-2fa">
            {String(auth.pendingTwoFactor)}
          </span>
        </div>
      );
    }

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>,
    );

    // Wait for refresh to settle
    await waitFor(() => {
      expect(screen.getByTestId('pending-2fa').textContent).toBe('false');
    });

    await user.click(screen.getByTestId('2fa-btn'));
    expect(screen.getByTestId('pending-2fa').textContent).toBe('true');
  });
});
