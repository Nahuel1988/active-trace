import { useContext } from 'react';
import { ComisionContext, type ComisionContextValue } from './ComisionContext';

export function useComisionContext(): ComisionContextValue {
  const context = useContext(ComisionContext);
  if (context === null) {
    throw new Error('useComisionContext must be used within a ComisionProvider');
  }
  return context;
}
