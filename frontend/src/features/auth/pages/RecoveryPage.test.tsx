// ── Tests: features/auth/pages/RecoveryPage ───────────────────────────────────
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

import RecoveryPage from './RecoveryPage';

describe('RecoveryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the recovery page with heading', () => {
    render(
      <MemoryRouter>
        <RecoveryPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('Restablecer contraseña')).toBeInTheDocument();
    expect(screen.getByLabelText('Email')).toBeInTheDocument();
  });
});
