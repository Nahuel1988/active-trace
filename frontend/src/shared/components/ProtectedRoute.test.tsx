// ── Tests: shared/components/ProtectedRoute ───────────────────────────────────
// Tasks 5.4, 5.5
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

// ── Mock api module for AuthProvider ────────────────────────────────────────
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

import { AuthProvider } from '@/shared/context/AuthContext';
import { ProtectedRoute } from './ProtectedRoute';

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApiPost.mockRejectedValue(new Error('no session'));
  });

  // ── 5.4: Sin sesión → redirige a /login con returnTo ────────────────────
  it('redirects to /login with returnTo when no session', async () => {
    const initialPath = '/some-protected-page';

    render(
      <MemoryRouter initialEntries={[initialPath]}>
        <AuthProvider>
          <Routes>
            <Route element={<ProtectedRoute />}>
              <Route
                path={initialPath}
                element={<div>Protected Content</div>}
              />
            </Route>
            <Route path="/login" element={<div>Login Page</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    );

    // Wait for refresh to settle → isAuthenticated = false → redirect to /login
    await waitFor(() => {
      expect(screen.getByText('Login Page')).toBeInTheDocument();
    });

    // Protected content should NOT be rendered
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  // ── 5.5: Con sesión pero sin permiso → redirige a /403 ──────────────────
  it('redirects to /403 when user lacks required permission', async () => {
    // Mock refresh to return a user WITHOUT liquidaciones:ver
    mockApiPost.mockResolvedValue({
      data: {
        user: {
          user_id: 'u1',
          tenant_id: 't1',
          roles: ['user'],
          permissions: ['estructura:gestionar'], // does NOT have liquidaciones:ver
        },
        access_token: 'token-123',
      },
    });

    render(
      <MemoryRouter initialEntries={['/protected-route']}>
        <AuthProvider>
          <Routes>
            <Route
              element={<ProtectedRoute permission="liquidaciones:ver" />}
            >
              <Route
                path="/protected-route"
                element={<div>Protected Content</div>}
              />
            </Route>
            <Route path="/403" element={<div>403 Forbidden</div>} />
            <Route path="/login" element={<div>Login Page</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    );

    // Wait for redirect to /403
    await waitFor(() => {
      expect(screen.getByText('403 Forbidden')).toBeInTheDocument();
    });

    // Protected content should NOT be rendered
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });
});
