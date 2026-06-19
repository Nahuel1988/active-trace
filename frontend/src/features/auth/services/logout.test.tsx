// ── Tests: logout limpia AuthContext y redirige incluso si falla ──────────────
// Task 5.8 — Se testea el componente AppLayout que contiene el handler de logout.
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

// ── Hoisted mocks ───────────────────────────────────────────────────────────
const { mockApiPost, mockLogout } = vi.hoisted(() => ({
  mockApiPost: vi.fn(),
  mockLogout: vi.fn(),
}));

// Mock api module for AuthProvider
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

// Mock authApi.logout to be controllable per test
vi.mock('@/features/auth/services/authApi', () => ({
  login: vi.fn(),
  verify2FA: vi.fn(),
  requestRecovery: vi.fn(),
  resetPassword: vi.fn(),
  refresh: vi.fn(),
  logout: mockLogout,
}));

import { AuthProvider } from '@/shared/context/AuthContext';
import AppLayout from '@/shared/components/AppLayout';

describe('logout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApiPost.mockResolvedValue({
      data: {
        user: {
          user_id: 'u1',
          tenant_id: 't1',
          roles: ['admin'],
          permissions: [],
        },
        access_token: 'token-123',
      },
    });
  });

  // ── 5.8: Logout limpia sesión y redirige incluso si la API falla ────────
  it('clears session and redirects to /login even when logout API fails', async () => {
    const user = userEvent.setup();

    // Mock logout to fail
    mockLogout.mockRejectedValue(new Error('Network error'));

    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <Routes>
            <Route element={<AppLayout />}>
              <Route path="/" element={<div>Home Page</div>} />
            </Route>
            <Route path="/login" element={<div>Login Page</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    );

    // Wait for auth to settle and layout to render
    await waitFor(() => {
      expect(screen.getByText('Cerrar sesión')).toBeInTheDocument();
    });

    // Click logout
    await user.click(screen.getByText('Cerrar sesión'));

    // Should navigate to /login even though the API call failed
    await waitFor(() => {
      expect(screen.getByText('Login Page')).toBeInTheDocument();
    });

    // Home page should no longer be shown
    expect(screen.queryByText('Home Page')).not.toBeInTheDocument();
  });
});
