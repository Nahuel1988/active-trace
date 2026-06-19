// ── Tests: shared/components/ForbiddenPage ────────────────────────────────────
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ForbiddenPage from './ForbiddenPage';

describe('ForbiddenPage', () => {
  it('renders 403 heading and message', () => {
    render(
      <MemoryRouter>
        <ForbiddenPage />
      </MemoryRouter>,
    );
    expect(screen.getByText('403')).toBeInTheDocument();
    expect(
      screen.getByText(/No tenés permisos para acceder a esta sección/i),
    ).toBeInTheDocument();
  });

  it('renders a link back to home', () => {
    render(
      <MemoryRouter>
        <ForbiddenPage />
      </MemoryRouter>,
    );
    const link = screen.getByRole('link', { name: /volver al inicio/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/');
  });
});
