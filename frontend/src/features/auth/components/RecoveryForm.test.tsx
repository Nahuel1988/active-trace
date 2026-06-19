// ── Tests: features/auth/components/RecoveryForm ──────────────────────────────
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';

const { mockRequestRecovery } = vi.hoisted(() => ({
  mockRequestRecovery: vi.fn(),
}));

vi.mock('@/features/auth/services/authApi', () => ({
  login: vi.fn(),
  verify2FA: vi.fn(),
  requestRecovery: mockRequestRecovery,
  resetPassword: vi.fn(),
  refresh: vi.fn(),
  logout: vi.fn(),
}));

import { RecoveryForm } from './RecoveryForm';

describe('RecoveryForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the recovery form with email field', () => {
    render(
      <MemoryRouter>
        <RecoveryForm />
      </MemoryRouter>,
    );

    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /enviar enlace/i }),
    ).toBeInTheDocument();
  });

  it('shows success message after submitting valid email', async () => {
    const user = userEvent.setup();
    mockRequestRecovery.mockResolvedValue(undefined);

    render(
      <MemoryRouter>
        <RecoveryForm />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText('Email'), 'test@example.com');
    await user.click(screen.getByRole('button', { name: /enviar enlace/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/revisá tu email/i),
      ).toBeInTheDocument();
    });
  });

  it('shows error when recovery API fails', async () => {
    const user = userEvent.setup();
    mockRequestRecovery.mockRejectedValue(new Error('Error de conexión'));

    render(
      <MemoryRouter>
        <RecoveryForm />
      </MemoryRouter>,
    );

    await user.type(screen.getByLabelText('Email'), 'test@example.com');
    await user.click(screen.getByRole('button', { name: /enviar enlace/i }));

    await waitFor(() => {
      expect(screen.getByText('Error de conexión')).toBeInTheDocument();
    });
  });
});
