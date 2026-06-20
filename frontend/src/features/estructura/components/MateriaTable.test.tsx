import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MateriaTable } from './MateriaTable';
import type { Materia } from '@/features/estructura/types';

const mockMaterias: Materia[] = [
  {
    id: 'm-1',
    tenant_id: 't',
    nombre: 'Programación I',
    clave_plus: 'PROG',
    created_at: '',
    updated_at: '',
  },
  {
    id: 'm-2',
    tenant_id: 't',
    nombre: 'Base de Datos',
    clave_plus: 'BD',
    created_at: '',
    updated_at: '',
  },
];

describe('MateriaTable', () => {
  it('estado vacío cuando no hay materias', () => {
    render(<MateriaTable materias={[]} />);
    expect(screen.getByText(/no hay materias registradas/i)).toBeInTheDocument();
  });

  it('renderiza la columna "Clave Plus" en el encabezado', () => {
    render(<MateriaTable materias={mockMaterias} />);
    expect(screen.getByText('Clave Plus')).toBeInTheDocument();
  });

  it('muestra la clave_plus de cada materia', () => {
    render(<MateriaTable materias={mockMaterias} />);
    expect(screen.getByText('PROG')).toBeInTheDocument();
    expect(screen.getByText('BD')).toBeInTheDocument();
  });

  it('muestra el nombre de cada materia', () => {
    render(<MateriaTable materias={mockMaterias} />);
    expect(screen.getByText('Programación I')).toBeInTheDocument();
    expect(screen.getByText('Base de Datos')).toBeInTheDocument();
  });

  it('muestra botón Editar cuando onEditar es provisto', () => {
    render(<MateriaTable materias={mockMaterias} onEditar={vi.fn()} />);
    const botonesEditar = screen.getAllByRole('button', { name: /editar/i });
    expect(botonesEditar).toHaveLength(mockMaterias.length);
  });

  it('no muestra columna de acciones sin onEditar', () => {
    render(<MateriaTable materias={mockMaterias} />);
    expect(screen.queryByRole('button', { name: /editar/i })).not.toBeInTheDocument();
  });
});
