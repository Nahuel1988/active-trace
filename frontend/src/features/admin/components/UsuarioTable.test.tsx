import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { UsuarioTable } from './UsuarioTable';
import type { Usuario } from '@/features/admin/types';

const mockUsuarios: Usuario[] = [
  {
    id: 'u-1',
    tenant_id: 't',
    legajo: 'L001',
    nombre: 'Ana',
    apellidos: 'López',
    email: 'ana@test.com',
    regional: 'GBA',
    facturador: true,
    is_active: true,
    created_at: '',
    updated_at: '',
  },
];

describe('UsuarioTable', () => {
  it('renders usuario name but NOT PII columns', () => {
    render(<UsuarioTable usuarios={mockUsuarios} />);
    expect(screen.getByText('Ana López')).toBeInTheDocument();
    // PII column headers must NOT be in the document
    expect(screen.queryByText(/^DNI$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^CUIL$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^CBU$/i)).not.toBeInTheDocument();
  });

  it('shows empty state when no usuarios', () => {
    render(<UsuarioTable usuarios={[]} />);
    expect(screen.getByText(/no hay usuarios/i)).toBeInTheDocument();
  });

  it('renders legajo and email for each usuario', () => {
    render(<UsuarioTable usuarios={mockUsuarios} />);
    expect(screen.getByText('L001')).toBeInTheDocument();
    expect(screen.getByText('ana@test.com')).toBeInTheDocument();
  });
});
