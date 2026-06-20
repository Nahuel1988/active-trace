import { useState } from 'react';
import { useAbonarFactura } from '@/features/finanzas/hooks/useFacturaMutations';

interface Props {
  facturaId: string;
  disabled?: boolean;
}

export function AbonarFacturaButton({ facturaId, disabled = false }: Props) {
  const [confirming, setConfirming] = useState(false);
  const [conflictError, setConflictError] = useState<string | null>(null);

  const { mutate, isPending } = useAbonarFactura();

  const handleAbonar = () => {
    setConflictError(null);
    mutate(facturaId, {
      onError: (err: unknown) => {
        const status =
          err instanceof Error && 'response' in (err as Record<string, unknown>)
            ? (err as { response?: { status?: number } }).response?.status
            : undefined;
        if (status === 409) {
          setConflictError('La factura ya fue abonada');
        }
        setConfirming(false);
      },
      onSuccess: () => {
        setConfirming(false);
      },
    });
  };

  if (confirming) {
    return (
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-700">¿Confirmar pago?</span>
          <button
            type="button"
            onClick={handleAbonar}
            disabled={isPending}
            className="rounded-md bg-green-600 px-3 py-1 text-xs font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            {isPending ? 'Procesando...' : 'Confirmar'}
          </button>
          <button
            type="button"
            onClick={() => {
              setConfirming(false);
              setConflictError(null);
            }}
            disabled={isPending}
            className="rounded-md border border-gray-300 px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Cancelar
          </button>
        </div>
        {conflictError && (
          <p className="text-xs text-red-600" role="alert">
            {conflictError}
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1">
      <button
        type="button"
        onClick={() => setConfirming(true)}
        disabled={disabled}
        className="rounded-md bg-green-600 px-3 py-1 text-xs font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-green-500"
      >
        Abonar
      </button>
      {conflictError && (
        <p className="text-xs text-red-600" role="alert">
          {conflictError}
        </p>
      )}
    </div>
  );
}
