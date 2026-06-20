// ── Tests: shared/services/api ───────────────────────────────────────────────
import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { AxiosRequestConfig } from 'axios';

// Helper: crea un adapter mock que controla qué respuestas devolver
interface MockResponse {
  data?: unknown;
  status?: number;
}

function createMockAdapter() {
  const responses = new Map<string, MockResponse>();
  let defaultResponse: MockResponse = { data: { ok: true }, status: 200 };

  const adapter = (config: AxiosRequestConfig) => {
    const match = config.url ? responses.get(config.url) : undefined;
    const { data, status } = match ?? defaultResponse;
    if (status && status >= 400) {
      return Promise.reject({
        response: { status, data },
        config,
        isAxiosError: true,
      });
    }
    return Promise.resolve({
      data: data ?? { ok: true },
      status: status ?? 200,
      statusText: 'OK',
      headers: {},
      config,
    });
  };

  return {
    adapter,
    setResponse: (url: string, spec: MockResponse) => {
      responses.set(url, spec);
    },
    setDefault: (spec: MockResponse) => {
      defaultResponse = spec;
    },
  };
}

describe('api module', () => {
  let mockAdapter: ReturnType<typeof createMockAdapter>;

  beforeEach(async () => {
    vi.resetModules();
    import.meta.env.VITE_API_URL = 'http://test.api';
    mockAdapter = createMockAdapter();
  });

  // ── 2.1: Instancia Axios centralizada ────────────────────────────────────
  describe('axios instance', () => {
    it('creates an axios instance with VITE_API_URL as baseURL', async () => {
      const { api } = await import('./api');
      expect(api.defaults.baseURL).toBe('http://test.api');
    });

    it('sets withCredentials to true', async () => {
      const { api } = await import('./api');
      expect(api.defaults.withCredentials).toBe(true);
    });

    it('does not use localStorage for token', async () => {
      const { setAccessToken, getAccessToken } = await import('./api');
      const spy = vi.spyOn(Storage.prototype, 'setItem');
      setAccessToken('test-token');
      expect(spy).not.toHaveBeenCalled();
      expect(getAccessToken()).toBe('test-token');
      spy.mockRestore();
    });
  });

  // ── Token management ─────────────────────────────────────────────────────
  describe('token management', () => {
    it('setAccessToken / getAccessToken works', async () => {
      const { setAccessToken, getAccessToken } = await import('./api');
      expect(getAccessToken()).toBeNull();
      setAccessToken('my-token');
      expect(getAccessToken()).toBe('my-token');
      setAccessToken(null);
      expect(getAccessToken()).toBeNull();
    });
  });

  // ── ForbiddenError ───────────────────────────────────────────────────────
  describe('ForbiddenError', () => {
    it('extends Error with name ForbiddenError', async () => {
      const { ForbiddenError } = await import('./api');
      const err = new ForbiddenError();
      expect(err).toBeInstanceOf(Error);
      expect(err.name).toBe('ForbiddenError');
      expect(err.message).toBe('Forbidden');
    });

    it('accepts custom message', async () => {
      const { ForbiddenError } = await import('./api');
      const err = new ForbiddenError('Sin permiso');
      expect(err.message).toBe('Sin permiso');
    });
  });

  // ── 2.4: Request interceptor ─────────────────────────────────────────────
  describe('request interceptor', () => {
    it('adds Authorization header when token is set', async () => {
      const { api, setAccessToken } = await import('./api');
      setAccessToken('valid-token');

      // Usar spy adapter para capturar la config de la request
      const adapterSpy = vi.fn().mockImplementation(mockAdapter.adapter);
      api.defaults.adapter = adapterSpy as any;

      await api.get('/test');

      const config = adapterSpy.mock.calls[0][0] as { headers: Record<string, string> };
      expect(config.headers.Authorization).toBe('Bearer valid-token');
    });

    it('does not add Authorization header when no token', async () => {
      const { api, setAccessToken } = await import('./api');
      setAccessToken(null);

      const adapterSpy = vi.fn().mockImplementation(mockAdapter.adapter);
      api.defaults.adapter = adapterSpy as any;

      await api.get('/test');

      const config = adapterSpy.mock.calls[0][0] as { headers: Record<string, string> };
      expect(config.headers.Authorization).toBeUndefined();
    });
  });

  // ── 2.6: Response interceptor (403) ─────────────────────────────────────
  describe('response interceptor — 403', () => {
    it('rejects with ForbiddenError on 403', async () => {
      const { api, ForbiddenError } = await import('./api');
      api.defaults.adapter = mockAdapter.adapter as any;
      mockAdapter.setDefault({ status: 403 });

      try {
        await api.get('/api/admin');
        expect.unreachable('Should have thrown');
      } catch (error) {
        expect(error).toBeInstanceOf(ForbiddenError);
      }
    });

    it('passes through non-403 errors', async () => {
      const { api } = await import('./api');
      api.defaults.adapter = mockAdapter.adapter as any;
      mockAdapter.setDefault({ status: 500 });

      try {
        await api.get('/api/error');
        expect.unreachable('Should have thrown');
      } catch (error: any) {
        expect(error.isAxiosError).toBe(true);
        expect(error.response.status).toBe(500);
      }
    });
  });

  // ── 2.5: Response interceptor (401 refresh flow) ─────────────────────────
  describe('response interceptor — 401 refresh', () => {
    it('refresh endpoint failure calls onSessionExpired handler', async () => {
      const { api, setOnSessionExpired } = await import('./api');
      api.defaults.adapter = mockAdapter.adapter as any;

      const onSessionExpired = vi.fn();
      setOnSessionExpired(onSessionExpired);

      // La request original devuelve 401, el refresh también 401
      mockAdapter.setDefault({ status: 401 });
      mockAdapter.setResponse('/api/auth/refresh', { status: 401 });

      await expect(api.get('/api/protected')).rejects.toThrow();
      // El handler registrado debe invocarse (AuthContext redirige a /login)
      expect(onSessionExpired).toHaveBeenCalled();
    });

    it('refresh success retries the original request', async () => {
      const { api, getAccessToken } = await import('./api');
      api.defaults.adapter = mockAdapter.adapter as any;

      // Configurar: llamadas a GET devuelven 401 la primera vez,
      // refresh devuelve nuevo token
      const refreshCall = vi.fn();
      let callCount = 0;

      const trackingAdapter = (config: { url?: string; method?: string }) => {
        if (config.url === '/api/auth/refresh') {
          refreshCall();
          return Promise.resolve({
            data: { access_token: 'refreshed-token' },
            status: 200,
            statusText: 'OK',
            headers: {},
            config,
          });
        }
        // Primer GET → 401, segundo GET (retry) → 200
        if (config.url === '/api/data') {
          callCount++;
          if (callCount === 1) {
            return Promise.reject({
              response: { status: 401 },
              config,
              isAxiosError: true,
            });
          }
        }
        return Promise.resolve({
          data: { success: true },
          status: 200,
          statusText: 'OK',
          headers: {},
          config,
        });
      };

      api.defaults.adapter = trackingAdapter as any;

      const response = await api.get('/api/data');
      expect(response.data).toEqual({ success: true });
      // Debería haberse llamado refresh exactamente una vez
      expect(refreshCall).toHaveBeenCalledTimes(1);
      // El token debería haberse actualizado
      expect(getAccessToken()).toBe('refreshed-token');
    });
  });

  // ── Session expired callback ─────────────────────────────────────────────
  describe('session expired callback', () => {
    it('setOnSessionExpired registers and clears handler', async () => {
      const { setOnSessionExpired } = await import('./api');
      const handler = vi.fn();
      setOnSessionExpired(handler);
      setOnSessionExpired(null);
      setOnSessionExpired(handler);
    });
  });
});
