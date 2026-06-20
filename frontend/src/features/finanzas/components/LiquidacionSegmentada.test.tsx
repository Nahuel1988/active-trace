import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LiquidacionSegmentada } from './LiquidacionSegmentada';
import type { LiquidacionVista } from '@/features/finanzas/types';

const mockVista: LiquidacionVista = {
  segmentos: {
    general: {
      liquidaciones: [
        { id: 'liq-1', tenant_id: 't', cohorte_id: 'c', periodo: '2026-06', usuario_id: 'u-1', rol: 'PROFESOR', comisiones: [], monto_base: '1000', monto_plus: '0', total: '1000', es_nexo: false, excluido_por_factura: false, estado: 'Abierta', created_at: '', updated_at: '' },
      ],
      subtotal: '1000',
    },
    nexo: {
      liquidaciones: [
        { id: 'liq-2', tenant_id: 't', cohorte_id: 'c', periodo: '2026-06', usuario_id: 'u-2', rol: 'NEXO', comisiones: [], monto_base: '500', monto_plus: '0', total: '500', es_nexo: true, excluido_por_factura: false, estado: 'Abierta', created_at: '', updated_at: '' },
      ],
      subtotal: '500',
    },
    facturantes: {
      liquidaciones: [
        { id: 'liq-3', tenant_id: 't', cohorte_id: 'c', periodo: '2026-06', usuario_id: 'u-3', rol: 'TUTOR', comisiones: [], monto_base: '800', monto_plus: '0', total: '800', es_nexo: false, excluido_por_factura: true, estado: 'Abierta', created_at: '', updated_at: '' },
      ],
      subtotal: '800',
    },
  },
  kpis: { total_sin_factura: '1500', total_con_factura: '2300' },
};

describe('LiquidacionSegmentada', () => {
  it('renders tres segmentos con datos mock', () => {
    render(<LiquidacionSegmentada vista={mockVista} />);
    expect(screen.getByText('General')).toBeInTheDocument();
    expect(screen.getAllByText('NEXO').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Facturantes')).toBeInTheDocument();
  });

  it('renderiza los 2 KPIs de cabecera', () => {
    render(<LiquidacionSegmentada vista={mockVista} />);
    expect(screen.getByText('Total sin factura')).toBeInTheDocument();
    expect(screen.getByText('Total con factura')).toBeInTheDocument();
  });

  it('muestra estado vacío cuando todos los segmentos están vacíos', () => {
    const empty: LiquidacionVista = {
      segmentos: {
        general: { liquidaciones: [], subtotal: '0' },
        nexo: { liquidaciones: [], subtotal: '0' },
        facturantes: { liquidaciones: [], subtotal: '0' },
      },
      kpis: { total_sin_factura: '0', total_con_factura: '0' },
    };
    render(<LiquidacionSegmentada vista={empty} />);
    expect(screen.getByText('Sin liquidaciones para el período')).toBeInTheDocument();
  });
});
