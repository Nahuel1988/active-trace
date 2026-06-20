import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AuditLogTable } from './AuditLogTable';
import type { AuditLogItem } from '@/features/admin/types';

const mockItems: AuditLogItem[] = [
  {
    id: 'log-1',
    tenant_id: 't',
    actor_id: 'u-1',
    actor_nombre: 'Ana López',
    materia_id: 'm-1',
    materia_nombre: 'Programación',
    accion: 'CREATE_ALUMNO',
    filas_afectadas: 1,
    ip: '192.168.1.1',
    user_agent: 'Mozilla/5.0',
    fecha_hora: '2026-06-01T10:00:00Z',
  },
];

describe('AuditLogTable', () => {
  it('muestra estado vacío cuando no hay items', () => {
    render(<AuditLogTable items={[]} />);
    expect(screen.getByText(/no hay registros de auditoría/i)).toBeInTheDocument();
  });

  it('renderiza los 7 encabezados de columna', () => {
    render(<AuditLogTable items={mockItems} />);
    expect(screen.getByText(/fecha \/ hora/i)).toBeInTheDocument();
    expect(screen.getByText(/actor/i)).toBeInTheDocument();
    expect(screen.getByText(/materia/i)).toBeInTheDocument();
    expect(screen.getByText(/acción/i)).toBeInTheDocument();
    expect(screen.getByText(/filas/i)).toBeInTheDocument();
    expect(screen.getByText(/^IP$/i)).toBeInTheDocument();
    expect(screen.getByText(/user agent/i)).toBeInTheDocument();
  });

  it('muestra los datos de un registro', () => {
    render(<AuditLogTable items={mockItems} />);
    expect(screen.getByText('Ana López')).toBeInTheDocument();
    expect(screen.getByText('Programación')).toBeInTheDocument();
    expect(screen.getByText('CREATE_ALUMNO')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('192.168.1.1')).toBeInTheDocument();
  });

  it('muestra "—" cuando materia_nombre es null', () => {
    const itemSinMateria: AuditLogItem = { ...mockItems[0], materia_id: null, materia_nombre: null };
    render(<AuditLogTable items={[itemSinMateria]} />);
    expect(screen.getByText('—')).toBeInTheDocument();
  });
});
