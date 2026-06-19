// ── Tests: shared/components/Spinner ──────────────────────────────────────────
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Spinner } from './Spinner';

describe('Spinner', () => {
  it('renders with sr-only loading text', () => {
    render(<Spinner />);
    expect(screen.getByText('Cargando...')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<Spinner className="extra-class" />);
    const outerDiv = container.firstChild as HTMLElement;
    expect(outerDiv.className).toContain('extra-class');
  });
});
