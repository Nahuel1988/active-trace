import { AgendaTable } from '../components/AgendaTable';

export default function ColoquiosAgendaPage() {
  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold text-gray-900">Agenda de coloquios</h1>
      <AgendaTable />
    </div>
  );
}
