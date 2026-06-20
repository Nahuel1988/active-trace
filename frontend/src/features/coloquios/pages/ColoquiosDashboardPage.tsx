import { useState } from 'react';
import { MetricasPanel } from '../components/MetricasPanel';
import { ColoquioTable } from '../components/ColoquioTable';
import { ColoquioFormDialog } from '../components/ColoquioFormDialog';

export default function ColoquiosDashboardPage() {
  const [dialogOpen, setDialogOpen] = useState(false);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Coloquios</h1>
        <button
          onClick={() => setDialogOpen(true)}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          Nueva convocatoria
        </button>
      </div>
      <MetricasPanel />
      <ColoquioTable />
      <ColoquioFormDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
      />
    </div>
  );
}
