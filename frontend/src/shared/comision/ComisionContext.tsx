import { createContext, type ReactNode } from 'react';
import { useSearchParams } from 'react-router-dom';

export interface ComisionContextValue {
  materia_id: string;
  cohorte_id: string;
  setComision: (materia_id: string, cohorte_id: string) => void;
}

export const ComisionContext = createContext<ComisionContextValue | null>(null);

export function ComisionProvider({ children }: { children: ReactNode }) {
  const [searchParams, setSearchParams] = useSearchParams();

  const materia_id = searchParams.get('materia') ?? '';
  const cohorte_id = searchParams.get('cohorte') ?? '';

  const setComision = (newMateriaId: string, newCohorteId: string) => {
    setSearchParams(
      (prev) => {
        if (newMateriaId) {
          prev.set('materia', newMateriaId);
        } else {
          prev.delete('materia');
        }
        if (newCohorteId) {
          prev.set('cohorte', newCohorteId);
        } else {
          prev.delete('cohorte');
        }
        return prev;
      },
      { replace: true },
    );
  };

  return (
    <ComisionContext.Provider value={{ materia_id, cohorte_id, setComision }}>
      {children}
    </ComisionContext.Provider>
  );
}
