import { RegistroAcademicoTable } from '../components/RegistroAcademicoTable';

export default function RegistroAcademicoPage() {
  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold text-gray-900">
        Registro académico
      </h1>
      <RegistroAcademicoTable />
    </div>
  );
}
