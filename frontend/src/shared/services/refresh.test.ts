// ── Tests: shared/services/refresh ────────────────────────────────────────────
// Tasks 5.6, 5.7 — Refresh transparente y cola de requests simultáneas
//
// NOTA: Estos tests NO mockean el módulo api. Usan la implementación real
// con un adapter mock que controla las respuestas de Axios.
import { describe, it, expect, vi, beforeEach } from 'vitest';

describe('refresh transparente', () => {
  beforeEach(async () => {
    vi.resetModules();
    // Configurar VITE_API_URL para que la instancia Axios se cree con un baseURL
    vi.stubEnv('VITE_API_URL', 'http://test.api');
  });

  // ── 5.6: 401 seguido de refresh exitoso reintenta la request original ────
  it('retries the original request after a 401 and successful refresh', async () => {
    const { api, getAccessToken, setOnSessionExpired } = await import('./api');

    const refreshCall = vi.fn();
    let callCount = 0;

    const trackingAdapter = (config: { url?: string; method?: string }) => {
      // Refresh endpoint devuelve nuevo token siempre
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

      // Primera request a /api/data → 401, segunda → 200
      if (config.url === '/api/data') {
        callCount++;
        if (callCount === 1) {
          return Promise.reject({
            response: { status: 401, data: { message: 'Unauthorized' } },
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

    // Registrar handler para evitar redirect en test
    const sessionExpiredHandler = vi.fn();
    setOnSessionExpired(sessionExpiredHandler);

    api.defaults.adapter = trackingAdapter as any;

    const response = await api.get('/api/data');

    // La request original debe haberse reintentado exitosamente
    expect(response.data).toEqual({ success: true });
    // Refresh debe haberse llamado exactamente una vez
    expect(refreshCall).toHaveBeenCalledTimes(1);
    // El token debe haberse actualizado
    expect(getAccessToken()).toBe('refreshed-token');
    // El handler de sesión expirada NO debe haberse llamado
    expect(sessionExpiredHandler).not.toHaveBeenCalled();
  });

  // ── 5.7: Múltiples 401 simultáneos → exactamente un POST /api/auth/refresh ─
  it('multiple concurrent 401s produce exactly one refresh call', async () => {
    const { api, getAccessToken } = await import('./api');

    let refreshCount = 0;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let resolveRefresh: (value: any) => void;

    // Promesa diferida para controlar cuándo se completa el refresh
    const deferred = new Promise<{ data: { access_token: string } }>(
      (resolve) => {
        resolveRefresh = resolve;
      },
    );

    // Contador de llamadas por URL para manejar reintentos
    const callCounts = new Map<string, number>();

    const adapter = (config: { url?: string; method?: string }) => {
      const url = config.url ?? 'unknown';

      // Refresh endpoint → promesa diferida (para que otras requests se encolen)
      if (url === '/api/auth/refresh') {
        refreshCount++;
        return deferred.then((result) => ({
          ...result,
          status: 200,
          statusText: 'OK',
          headers: {},
          config,
        }));
      }

      // Todas las demás requests: primera vez → 401, reintento → 200
      const count = callCounts.get(url) ?? 0;
      callCounts.set(url, count + 1);

      if (count === 0) {
        return Promise.reject({
          response: { status: 401, data: { message: 'Unauthorized' } },
          config,
          isAxiosError: true,
        });
      }

      return Promise.resolve({
        data: { success: true, url },
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      });
    };

    api.defaults.adapter = adapter as any;

    // Disparar 3 requests simultáneas
    const promise1 = api.get('/api/data1').catch((e) => e);
    const promise2 = api.get('/api/data2').catch((e) => e);
    const promise3 = api.get('/api/data3').catch((e) => e);

    // Esperar a que los microtasks se procesen:
    // Acá se ejecutan los interceptores de request/response para las 3 requests
    await new Promise<void>((resolve) => setTimeout(resolve, 0));

    // El refresh debe haberse invocado exactamente una vez
    expect(refreshCount).toBe(1);

    // Resolver el refresh para que todas las requests encoladas continúen
    resolveRefresh!({ data: { access_token: 'refreshed-token' } });

    // Esperar a que todas las requests se resuelvan
    const results = await Promise.all([promise1, promise2, promise3]);

    // Todas deben haber completado
    expect(results).toHaveLength(3);
    // refresh debe haberse llamado exactamente una vez
    expect(refreshCount).toBe(1);
    // Token debe estar actualizado
    expect(getAccessToken()).toBe('refreshed-token');
  });
});
