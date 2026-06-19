// ── useAuth ──────────────────────────────────────────────────────────────────
// Hook que consume AuthContext. Lanza error si se usa fuera de AuthProvider.

import { useContext } from 'react';
import { AuthContext, type AuthContextValue } from '@/shared/context/AuthContext';

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
