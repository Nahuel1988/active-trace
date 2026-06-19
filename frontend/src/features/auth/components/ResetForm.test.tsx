// ── Tests: features/auth/components/ResetForm ─────────────────────────────────
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';

const { mockResetPassword, mockNavigate } = vi.hoisted(() => ({
  mockResetPassword: vi.fn(),
  mockNavigate: vi.fn(),
}));

vi.mock('@/features/auth/services/authApi', () => ({
  login: vi.fn(),
  verify2FA: vi.fn(),
  requestRecovery: vi.fn(),
  resetPassword: mockResetPassword,
  refresh: vi.fn(),
  logout: vi.fn(),
}));

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

import { ResetForm } from './ResetForm';

describe('ResetForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders error when no token in URL', () => {
    render(
      <MemoryRouter initialEntries={['/auth/reset']}>
        <ResetForm />
      </MemoryRouter>,
    );

    expect(
      screen.getByText(/enlace inválido o expirado/i),
    ).toBeInTheDocument();
  });

  it('renders password fields when token is present', () => {
    render(
      <MemoryRouter initialEntries={['/auth/reset?token=abc123']}>
        <ResetForm />
      </MemoryRouter>,
    );

    expect(screen.getByLabelText('Nueva contraseña')).toBeInTheDocument();
    expect(screen.getByLabelText('Confirmar contraseña')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /restablecer contraseña/i }),
    ).toBeInTheDocument();
  });

  it('calls resetPassword and redirects on success', async () => {
    const user = userEvent.setup();
    mockResetPassword.mockResolvedValue(undefined);

    render(
      <MemoryRouter initialEntries={['/auth/reset?token=abc123']}>
        <ResetForm />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText('Nueva contraseña'), 'newpass123');
    await user.type(screen.getByLabelText('Confirmar contraseña'), 'newpass123');
    await user.click(
      screen.getByRole('button', { name: /restablecer contraseña/i }),
    );

    await waitFor(() => {
      expect(mockResetPassword).toHaveBeenCalledWith({
        token: 'abc123',
        password: 'newpass123',
        confirm_password: 'newpass123',
      });
    });

    expect(mockNavigate).toHaveBeenCalledWith('/login', { replace: true });
  });

  it('shows error when reset fails', async () => {
    const user = userEvent.setup();
    mockResetPassword.mockRejectedValue(new Error('Token inválido'));

    render(
      <MemoryRouter initialEntries={['/auth/reset?token=abc123']}>
        <ResetForm />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText('Nueva contraseña'), 'newpass123');
    await user.type(screen.getByLabelText('Confirmar contraseña'), 'newpass123');
    await user.click(
      screen.getByRole('button', { name: /restablecer contraseña/i }),
    );

    await waitFor(() => {
      expect(screen.getByText('Token inválido')).toBeInTheDocument();
    });
  });
});
