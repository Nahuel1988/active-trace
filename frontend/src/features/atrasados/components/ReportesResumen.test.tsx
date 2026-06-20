import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ReportesResumen } from './ReportesResumen';
import { NotasFinalesTable } from './NotasFinalesTable';

describe('ReportesResumen', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  const reportes = { total_alumnos: 30, total_actividades: 10, tasa_abrobacion_pct: 65.5, alumnos_atrasados: 8, alumnos_al_dia: 22, sin_datos: false };

  it('renders reportes data', () => {
    render(<ReportesResumen data={reportes} />);

    expect(screen.getByText('30')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.getByText('65.5%')).toBeInTheDocument();
    expect(screen.getByText('8')).toBeInTheDocument();
    expect(screen.getByText('22')).toBeInTheDocument();
  });

  it('shows empty state when sin_datos', () => {
    render(<ReportesResumen data={{ total_alumnos: 0, total_actividades: 0, tasa_abrobacion_pct: 0, alumnos_atrasados: 0, alumnos_al_dia: 0, sin_datos: true }} />);

    expect(screen.getByText('No hay datos disponibles para esta comisión')).toBeInTheDocument();
  });
});

describe('NotasFinalesTable', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  const notas = [
    { entrada_padron_id: '1', alumno_nombre: 'Juan', alumno_apellido: 'Pérez', nota_final: 8.5, condicion: 'promocionado' },
    { entrada_padron_id: '2', alumno_nombre: 'María', alumno_apellido: 'García', nota_final: 4, condicion: 'regular' },
  ];

  it('renders notas finales', () => {
    render(<NotasFinalesTable items={notas} />);

    expect(screen.getByText('Pérez')).toBeInTheDocument();
    expect(screen.getByText('8.5')).toBeInTheDocument();
    expect(screen.getByText('promocionado')).toBeInTheDocument();
  });

  it('shows empty state', () => {
    render(<NotasFinalesTable items={[]} />);

    expect(screen.getByText('No hay notas finales registradas')).toBeInTheDocument();
  });
});
