import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuditLogFilters } from './AuditLogFilters';
import type { AuditLogFilters as AuditLogFiltersType } from '@/features/admin/types';

describe('AuditLogFilters', () => {
  it('renderiza los 4 campos de filtro', () => {
    render(<AuditLogFilters filters={{}} onChange={vi.fn()} />);
    expect(screen.getByLabelText(/desde/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/hasta/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/materia id/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/acción/i)).toBeInTheDocument();
  });

  it('cambio de "desde" llama onChange con el valor actualizado', async () => {
    const onChange = vi.fn();
    render(<AuditLogFilters filters={{}} onChange={onChange} />);
    await userEvent.type(screen.getByLabelText(/desde/i), '2026-06-01');
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ desde: expect.any(String) }));
  });

  it('cambio de materia_id llama onChange con el campo actualizado', async () => {
    const onChange = vi.fn();
    render(<AuditLogFilters filters={{}} onChange={onChange} />);
    await userEvent.type(screen.getByLabelText(/materia id/i), 'abc-123');
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ materia_id: expect.any(String) }));
  });

  it('cambio de acción llama onChange con el campo actualizado', async () => {
    const onChange = vi.fn();
    render(<AuditLogFilters filters={{}} onChange={onChange} />);
    await userEvent.type(screen.getByLabelText(/acción/i), 'CREATE');
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ accion: expect.any(String) }));
  });

  it('refleja los filtros actuales en los inputs controlados', () => {
    const filters: AuditLogFiltersType = { desde: '2026-01-01', accion: 'LOGIN' };
    render(<AuditLogFilters filters={filters} onChange={vi.fn()} />);
    expect(screen.getByLabelText<HTMLInputElement>(/desde/i).value).toBe('2026-01-01');
    expect(screen.getByLabelText<HTMLInputElement>(/acción/i).value).toBe('LOGIN');
  });
});
