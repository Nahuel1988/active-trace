import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ComunicacionPreview } from './ComunicacionPreview';

const previewItems = [
  { destinatario: 'a@b.com', asunto_render: 'Hola Juan', cuerpo_render: 'Tu nota es 8' },
  { destinatario: 'c@d.com', asunto_render: 'Hola María', cuerpo_render: 'Tu nota es 6' },
];

describe('ComunicacionPreview', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows asunto and cuerpo per destinatario', () => {
    render(<ComunicacionPreview items={previewItems} onConfirm={vi.fn()} onBack={vi.fn()} isPending={false} />);

    expect(screen.getByText('a@b.com')).toBeInTheDocument();
    expect(screen.getByText('Hola Juan')).toBeInTheDocument();
    expect(screen.getByText('Tu nota es 8')).toBeInTheDocument();
    expect(screen.getByText('c@d.com')).toBeInTheDocument();
    expect(screen.getByText('Hola María')).toBeInTheDocument();
  });

  it('confirm button triggers onConfirm', async () => {
    const onConfirm = vi.fn();
    const user = userEvent.setup();

    render(<ComunicacionPreview items={previewItems} onConfirm={onConfirm} onBack={vi.fn()} isPending={false} />);

    await user.click(screen.getByText('Enviar comunicaciones'));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('back button triggers onBack', async () => {
    const onBack = vi.fn();
    const user = userEvent.setup();

    render(<ComunicacionPreview items={previewItems} onConfirm={vi.fn()} onBack={onBack} isPending={false} />);

    await user.click(screen.getByText('Volver'));
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it('shows loading state when isPending', () => {
    render(<ComunicacionPreview items={previewItems} onConfirm={vi.fn()} onBack={vi.fn()} isPending={true} />);

    expect(screen.getByText('Enviando...')).toBeInTheDocument();
  });
});
