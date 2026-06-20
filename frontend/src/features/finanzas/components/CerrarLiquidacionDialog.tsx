interface Props {
  open: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  isPending: boolean;
  error: string | null;
}

export function CerrarLiquidacionDialog({ open, onConfirm, onCancel, isPending, error }: Props) {
  if (!open) return null;

  return (
    <div role="dialog" aria-modal className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Cerrar liquidación</h2>
        <p className="text-sm text-gray-600 mb-4">
          Una vez cerrada, la liquidación no podrá modificarse. ¿Confirmás?
        </p>
        {error && (
          <p className="text-sm text-red-600 mb-4" role="alert">
            {error}
          </p>
        )}
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm rounded-lg border border-gray-300 hover:bg-gray-50"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            disabled={isPending}
            className="px-4 py-2 text-sm rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Confirmar
          </button>
        </div>
      </div>
    </div>
  );
}
