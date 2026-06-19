// ── Tests: features/auth/pages/LoginPage ──────────────────────────────────────
// Tasks 5.1, 5.2, 5.3
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';

// ── Hoisted mocks ───────────────────────────────────────────────────────────
const { mockApiPost, mockLogin, mockNavigate } = vi.hoisted(() => ({
  mockApiPost: vi.fn(),
  mockLogin: vi.fn(),
  mockNavigate: vi.fn(),
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

// Mock authApi for useLogin
vi.mock('@/features/auth/services/authApi', () => ({
  login: mockLogin,
  verify2FA: vi.fn(),
  requestRecovery: vi.fn(),
  resetPassword: vi.fn(),
  refresh: vi.fn(),
  logout: vi.fn(),
}));

// Mock react-router-dom to spy on useNavigate
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

import { AuthProvider } from '@/shared/context/AuthContext';
import LoginPage from '@/features/auth/pages/LoginPage';

function renderLoginPage() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApiPost.mockRejectedValue(new Error('no session'));
    mockLogin.mockReset();
    mockNavigate.mockReset();
  });

  // ── 5.1: Renderiza formulario sin errores ────────────────────────────────
  it('renders the login form without errors', async () => {
    renderLoginPage();

    // Wait for AuthProvider refresh to settle
    await waitFor(() => {
      expect(screen.getByText('Iniciar sesión')).toBeInTheDocument();
    });

    // Form fields should be present
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Contraseña')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /ingresar/i }),
    ).toBeInTheDocument();
  });

  // ── 5.2: Login exitoso sin 2FA ───────────────────────────────────────────
  it('calls setSession and redirects on successful login without 2FA', async () => {
    const user = userEvent.setup();

    mockLogin.mockResolvedValue({
      user: {
        user_id: 'u1',
        tenant_id: 't1',
        roles: ['tutor'],
        permissions: [],
      },
      access_token: 'token-abc-123',
      requires_2fa: false,
    });

    renderLoginPage();

    await waitFor(() => {
      expect(screen.getByLabelText('Email')).toBeInTheDocument();
    });

    // Fill form
    await user.type(screen.getByLabelText('Email'), 'test@example.com');
    await user.type(screen.getByLabelText('Contraseña'), 'password123');

    // Submit
    await user.click(screen.getByRole('button', { name: /ingresar/i }));

    // Wait for login to complete
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
      });
    });

    // Should navigate to / (default returnTo)
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/', { replace: true });
    });
  });

  // ── 5.3: Login con credenciales inválidas ────────────────────────────────
  it('shows error message when credentials are invalid', async () => {
    const user = userEvent.setup();

    mockLogin.mockRejectedValue(new Error('Credenciales inválidas'));

    renderLoginPage();

    await waitFor(() => {
      expect(screen.getByLabelText('Email')).toBeInTheDocument();
    });

    // Fill form
    await user.type(screen.getByLabelText('Email'), 'wrong@example.com');
    await user.type(screen.getByLabelText('Contraseña'), 'wrongpass');

    // Submit
    await user.click(screen.getByRole('button', { name: /ingresar/i }));

    // Error message should appear
    await waitFor(() => {
      expect(screen.getByText('Credenciales inválidas')).toBeInTheDocument();
    });

    // Should NOT have navigated
    expect(mockNavigate).not.toHaveBeenCalled();
  });
});
