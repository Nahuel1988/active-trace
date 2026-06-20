import { Link } from 'react-router-dom';

export default function EstructuraHomePage() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Estructura académica</h1>
        <p className="mt-1 text-sm text-gray-500">Administrá carreras, cohortes y materias de la institución.</p>
      </div>
      <nav className="grid gap-4 sm:grid-cols-3">
        <Link
          to="/estructura/carreras"
          className="rounded-lg border border-gray-200 p-5 hover:border-indigo-400 hover:shadow-sm transition-shadow"
        >
          <h2 className="font-semibold text-gray-900">Carreras</h2>
          <p className="mt-1 text-sm text-gray-500">Gestión de carreras habilitadas.</p>
        </Link>
        <Link
          to="/estructura/cohortes"
          className="rounded-lg border border-gray-200 p-5 hover:border-indigo-400 hover:shadow-sm transition-shadow"
        >
          <h2 className="font-semibold text-gray-900">Cohortes</h2>
          <p className="mt-1 text-sm text-gray-500">Cohortes académicas por carrera.</p>
        </Link>
        <Link
          to="/estructura/materias"
          className="rounded-lg border border-gray-200 p-5 hover:border-indigo-400 hover:shadow-sm transition-shadow"
        >
          <h2 className="font-semibold text-gray-900">Materias</h2>
          <p className="mt-1 text-sm text-gray-500">Materias y claves de Plus.</p>
        </Link>
      </nav>
    </div>
  );
}
