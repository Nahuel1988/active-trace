// ── Tests: features/auth/services/authApi ─────────────────────────────────────
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock api module to control axios calls
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
    defaults: {},
  },
  setAccessToken: vi.fn(),
  setOnSessionExpired: vi.fn(),
  getAccessToken: vi.fn(),
  ForbiddenError: class ForbiddenError extends Error {
    constructor(m?: string) { super(m ?? 'Forbidden'); this.name = 'ForbiddenError'; }
  },
}));

import * as authApi from './authApi';

describe('authApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('login posts to /api/auth/login with credentials', async () => {
    mockApiPost.mockResolvedValue({ data: { access_token: 't1', user: {} } });
    await authApi.login({ email: 'a@b.com', password: 'secret' });
    expect(mockApiPost).toHaveBeenCalledWith('/api/auth/login', {
      email: 'a@b.com',
      password: 'secret',
    });
  });

  it('verify2FA posts to /api/auth/2fa/verify with code', async () => {
    mockApiPost.mockResolvedValue({ data: { access_token: 't1', user: {} } });
    await authApi.verify2FA('123456');
    expect(mockApiPost).toHaveBeenCalledWith('/api/auth/2fa/verify', { code: '123456' });
  });

  it('requestRecovery posts to /api/auth/forgot with email', async () => {
    mockApiPost.mockResolvedValue({});
    await authApi.requestRecovery('a@b.com');
    expect(mockApiPost).toHaveBeenCalledWith('/api/auth/forgot', { email: 'a@b.com' });
  });

  it('resetPassword posts to /api/auth/reset with data', async () => {
    mockApiPost.mockResolvedValue({});
    const data = { token: 'abc', password: 'new123', confirm_password: 'new123' };
    await authApi.resetPassword(data);
    expect(mockApiPost).toHaveBeenCalledWith('/api/auth/reset', data);
  });

  it('refresh posts to /api/auth/refresh', async () => {
    mockApiPost.mockResolvedValue({ data: { access_token: 't1', user: {} } });
    await authApi.refresh();
    expect(mockApiPost).toHaveBeenCalledWith('/api/auth/refresh');
  });

  it('logout posts to /api/auth/logout', async () => {
    mockApiPost.mockResolvedValue({});
    await authApi.logout();
    expect(mockApiPost).toHaveBeenCalledWith('/api/auth/logout');
  });
});
