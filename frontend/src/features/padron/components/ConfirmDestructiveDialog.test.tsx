import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ConfirmDestructiveDialog } from './ConfirmDestructiveDialog';

describe('ConfirmDestructiveDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('does not fire onConfirm without confirmation', () => {
    const onConfirm = vi.fn();
    const onCancel = vi.fn();

    render(
      <ConfirmDestructiveDialog
        open={true}
        title="Reemplazar padrón"
        description="Esto reemplazará el padrón actual"
        onConfirm={onConfirm}
        onCancel={onCancel}
      />,
    );

    expect(screen.getByText('Reemplazar padrón')).toBeInTheDocument();
    expect(screen.getByText('Esto reemplazará el padrón actual')).toBeInTheDocument();
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it('fires onCancel when cancel is clicked', async () => {
    const onCancel = vi.fn();
    const user = userEvent.setup();

    render(
      <ConfirmDestructiveDialog
        open={true}
        title="Reemplazar padrón"
        description="Esto reemplazará el padrón actual"
        onConfirm={vi.fn()}
        onCancel={onCancel}
      />,
    );

    await user.click(screen.getByText('Cancelar'));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('fires onConfirm when confirm is clicked', async () => {
    const onConfirm = vi.fn();
    const user = userEvent.setup();

    render(
      <ConfirmDestructiveDialog
        open={true}
        title="Reemplazar padrón"
        description="Esto reemplazará el padrón actual"
        onConfirm={onConfirm}
        onCancel={vi.fn()}
      />,
    );

    await user.click(screen.getByText('Sí, reemplazar'));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('does not render when open is false', () => {
    render(
      <ConfirmDestructiveDialog
        open={false}
        title="Reemplazar padrón"
        description="Esto reemplazará el padrón actual"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );

    expect(screen.queryByText('Reemplazar padrón')).not.toBeInTheDocument();
  });

  it('warns about destructive replacement (RN-05)', () => {
    render(
      <ConfirmDestructiveDialog
        open={true}
        title="Reemplazar padrón"
        description="Esto reemplazará el padrón actual de la materia"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );

    expect(screen.getByText(/reemplazará/i)).toBeInTheDocument();
  });
});
