// ── Tests: features/auth/pages/ResetPage ──────────────────────────────────────
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

vi.mock('@/features/auth/services/authApi', () => ({
  login: vi.fn(),
  verify2FA: vi.fn(),
  requestRecovery: vi.fn(),
  resetPassword: vi.fn(),
  refresh: vi.fn(),
  logout: vi.fn(),
}));

import ResetPage from './ResetPage';

describe('ResetPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the reset page with heading and form fields', () => {
    render(
      <MemoryRouter initialEntries={['/auth/reset?token=abc']}>
        <ResetPage />
      </MemoryRouter>,
    );

    expect(
      screen.getByText('Establecer nueva contraseña'),
    ).toBeInTheDocument();
    expect(screen.getByLabelText('Nueva contraseña')).toBeInTheDocument();
    expect(screen.getByLabelText('Confirmar contraseña')).toBeInTheDocument();
  });
});
