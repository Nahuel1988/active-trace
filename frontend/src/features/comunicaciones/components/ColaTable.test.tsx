import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ColaTable } from './ColaTable';
import type { ComunicacionResponse } from '@/features/comunicaciones/types';

const items: ComunicacionResponse[] = [
  { id: '1', lote_id: 'l1', destinatario: 'a@b.com', asunto: 'Hola', cuerpo: 'Cuerpo', estado: 'pendiente', requiere_aprobacion: true },
  { id: '2', lote_id: 'l1', destinatario: 'c@d.com', asunto: 'Chau', cuerpo: 'Cuerpo2', estado: 'enviado', requiere_aprobacion: false },
  { id: '3', lote_id: 'l2', destinatario: 'e@f.com', asunto: 'Test', cuerpo: 'Test', estado: 'error', requiere_aprobacion: false },
  { id: '4', lote_id: 'l2', destinatario: 'g@h.com', asunto: 'Cancel', cuerpo: 'Canc', estado: 'cancelado', requiere_aprobacion: false },
];

describe('ColaTable', () => {
  it('renders all rows', () => {
    render(<ColaTable items={items} onAprobar={vi.fn()} onCancelar={vi.fn()} isPending={false} />);
    expect(screen.getByText('a@b.com')).toBeInTheDocument();
    expect(screen.getByText('c@d.com')).toBeInTheDocument();
    expect(screen.getByText('e@f.com')).toBeInTheDocument();
  });

  it('shows estado badges', () => {
    render(<ColaTable items={items} onAprobar={vi.fn()} onCancelar={vi.fn()} isPending={false} />);

    expect(screen.getByText('pendiente')).toBeInTheDocument();
    expect(screen.getByText('enviado')).toBeInTheDocument();
    expect(screen.getByText('error')).toBeInTheDocument();
    expect(screen.getByText('cancelado')).toBeInTheDocument();
  });

  it('calls onAprobar for pendiente items', async () => {
    const onAprobar = vi.fn();
    const user = userEvent.setup();

    render(<ColaTable items={items} onAprobar={onAprobar} onCancelar={vi.fn()} isPending={false} canAprobar={true} />);

    const aprobarButtons = screen.getAllByText('Aprobar');
    expect(aprobarButtons).toHaveLength(1);
    await user.click(aprobarButtons[0]);
    expect(onAprobar).toHaveBeenCalledWith('l1');
  });

  it('calls onCancelar for pendiente items', async () => {
    const onCancelar = vi.fn();
    const user = userEvent.setup();

    render(<ColaTable items={items} onAprobar={vi.fn()} onCancelar={onCancelar} isPending={false} canAprobar={true} />);

    const cancelarButtons = screen.getAllByText('Cancelar');
    expect(cancelarButtons).toHaveLength(1);
    await user.click(cancelarButtons[0]);
    expect(onCancelar).toHaveBeenCalledWith('l1');
  });

  it('hides actions when canAprobar is false', () => {
    render(<ColaTable items={items} onAprobar={vi.fn()} onCancelar={vi.fn()} isPending={false} canAprobar={false} />);

    expect(screen.queryByText('Aprobar')).not.toBeInTheDocument();
    expect(screen.queryByText('Cancelar')).not.toBeInTheDocument();
  });
});
