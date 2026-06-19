// ── Tests: shared/hooks/usePermission ─────────────────────────────────────────
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

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

// Static imports — work because vitest hoists mocks
import { AuthProvider } from '@/shared/context/AuthContext';
import { useAuth } from '@/shared/hooks/useAuth';
import { usePermission } from './usePermission';

describe('usePermission', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApiPost.mockRejectedValue(new Error('no session'));
  });

  // ── 2.8: Sin sesión → false ─────────────────────────────────────────────
  it('returns false when user is not authenticated', async () => {
    function TestComponent() {
      const canRead = usePermission('users:read');
      return <span data-testid="can-read">{String(canRead)}</span>;
    }

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>,
    );

    // Wait for refresh to settle (isLoading → false, user stays null)
    await waitFor(() => {
      expect(screen.getByTestId('can-read').textContent).toBe('false');
    });
  });

  // ── 2.8: Con permiso existente → true ────────────────────────────────────
  it('returns true when user has the permission', async () => {
    const user = userEvent.setup();

    const mockUser = {
      user_id: 'u1',
      tenant_id: 't1',
      roles: ['admin'] as string[],
      permissions: ['users:read', 'users:write', 'grades:view'] as string[],
    };

    function PermissionTest() {
      const auth = useAuth();
      const canRead = usePermission('users:read');
      const canDelete = usePermission('users:delete');

      return (
        <div>
          <button
            data-testid="login-btn"
            onClick={() => auth.setSession(mockUser, 'token-123')}
          >
            Login
          </button>
          <span data-testid="can-read">{String(canRead)}</span>
          <span data-testid="can-delete">{String(canDelete)}</span>
        </div>
      );
    }

    render(
      <AuthProvider>
        <PermissionTest />
      </AuthProvider>,
    );

    // Wait for refresh to settle
    await waitFor(() => {
      expect(screen.getByTestId('can-read').textContent).toBe('false');
    });

    // Iniciar sesión
    await user.click(screen.getByTestId('login-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('can-read').textContent).toBe('true');
    });
    expect(screen.getByTestId('can-delete').textContent).toBe('false');
  });

  // ── 2.8: Sin sesión tras logout → false de nuevo ─────────────────────────
  it('returns false after logout', async () => {
    const user = userEvent.setup();

    const mockUser = {
      user_id: 'u1',
      tenant_id: 't1',
      roles: [] as string[],
      permissions: ['users:read'] as string[],
    };

    function AuthFlowTest() {
      const auth = useAuth();
      const canRead = usePermission('users:read');

      return (
        <div>
          <button
            data-testid="login-btn"
            onClick={() => auth.setSession(mockUser, 'token-123')}
          >
            Login
          </button>
          <button data-testid="logout-btn" onClick={() => auth.clearSession()}>
            Logout
          </button>
          <span data-testid="can-read">{String(canRead)}</span>
        </div>
      );
    }

    render(
      <AuthProvider>
        <AuthFlowTest />
      </AuthProvider>,
    );

    // Wait for refresh to settle
    await waitFor(() => {
      expect(screen.getByTestId('can-read').textContent).toBe('false');
    });

    // Login
    await user.click(screen.getByTestId('login-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('can-read').textContent).toBe('true');
    });

    // Logout
    await user.click(screen.getByTestId('logout-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('can-read').textContent).toBe('false');
    });
  });
});
