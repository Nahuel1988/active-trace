// ── Tests: features/auth/components/TwoFAGate ─────────────────────────────────
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const { mockApiPost, mockVerify2FA } = vi.hoisted(() => ({
  mockApiPost: vi.fn(),
  mockVerify2FA: vi.fn(),
}));

vi.mock('@/shared/services/api', () => ({
  api: {
    post: mockApiPost,
    get: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
    defaults: {},
  },
  setAccessToken: vi.fn(),
  setOnSessionExpired: vi.fn(),
  getAccessToken: vi.fn(),
  ForbiddenError: class ForbiddenError extends Error {
    constructor(m?: string) { super(m ?? 'Forbidden'); this.name = 'ForbiddenError'; }
  },
}));

vi.mock('@/features/auth/services/authApi', () => ({
  login: vi.fn(),
  verify2FA: mockVerify2FA,
  requestRecovery: vi.fn(),
  resetPassword: vi.fn(),
  refresh: vi.fn(),
  logout: vi.fn(),
}));

import { AuthProvider } from '@/shared/context/AuthContext';
import { TwoFAGate } from './TwoFAGate';

describe('TwoFAGate', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApiPost.mockRejectedValue(new Error('no session'));
  });

  it('renders the 2FA verification form', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <TwoFAGate />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByText(/código de verificación/i),
      ).toBeInTheDocument();
    });

    expect(
      screen.getByRole('button', { name: /verificar/i }),
    ).toBeInTheDocument();
  });

  it('shows validation error for incomplete code on submit', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <TwoFAGate />
        </AuthProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole('button', { name: /verificar/i }),
      ).toBeInTheDocument();
    });

    // Submit without filling code (button is disabled for < 6 digits)
    const button = screen.getByRole('button', { name: /verificar/i });

    // Button should be disabled when code is empty (isValidCode = false)
    expect(button).toBeDisabled();
  });
});
