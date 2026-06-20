import { useState, useRef, useEffect, useCallback } from 'react';
import type { EstadoGuardia } from '../types';

const ESTADO_COLOR: Record<EstadoGuardia, string> = {
  pendiente: 'bg-yellow-100 text-yellow-800',
  realizada: 'bg-green-100 text-green-800',
  cancelada: 'bg-red-100 text-red-800',
};

const ESTADO_LABEL: Record<EstadoGuardia, string> = {
  pendiente: 'Pendiente',
  realizada: 'Realizada',
  cancelada: 'Cancelada',
};

const TRANSICIONES: Partial<Record<EstadoGuardia, EstadoGuardia[]>> = {
  pendiente: ['realizada', 'cancelada'],
};

interface GuardiaEstadoBadgeProps {
  estado: EstadoGuardia;
  onChange?: (nuevoEstado: EstadoGuardia) => void;
  disabled?: boolean;
}

export function GuardiaEstadoBadge({
  estado,
  onChange,
  disabled = false,
}: GuardiaEstadoBadgeProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [open]);

  const handleSelect = useCallback(
    (nuevo: EstadoGuardia) => {
      onChange?.(nuevo);
      setOpen(false);
    },
    [onChange],
  );

  const transiciones = onChange ? TRANSICIONES[estado] : undefined;

  return (
    <div className="relative inline-block" ref={ref}>
      <button
        type="button"
        disabled={disabled || !transiciones}
        onClick={() => setOpen(!open)}
        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
          ESTADO_COLOR[estado]
        } ${
          transiciones ? 'cursor-pointer hover:opacity-80' : 'cursor-default'
        }`}
      >
        {ESTADO_LABEL[estado]}
        {transiciones && (
          <svg
            className="ml-1 h-3 w-3"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M19 9l-7 7-7-7"
            />
          </svg>
        )}
      </button>

      {open && transiciones && (
        <div className="absolute right-0 z-10 mt-1 w-36 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black/5">
          <div className="py-1">
            {transiciones.map((opcion) => (
              <button
                key={opcion}
                type="button"
                onClick={() => handleSelect(opcion)}
                className={`block w-full px-4 py-2 text-left text-xs ${
                  opcion === 'realizada'
                    ? 'text-green-700 hover:bg-green-50'
                    : 'text-red-700 hover:bg-red-50'
                }`}
              >
                Marcar como {ESTADO_LABEL[opcion].toLowerCase()}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
