import { Link, useParams } from 'react-router-dom';
import { TareaDetail } from '@/features/tareas/components/TareaDetail';

export default function TareaDetailPage() {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="p-6">
      <div className="mb-4">
        <Link
          to="/tareas"
          className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
        >
          &larr; Volver a tareas
        </Link>
      </div>
      {id ? (
        <TareaDetail />
      ) : (
        <p className="py-8 text-center text-gray-500">Tarea no encontrada.</p>
      )}
    </div>
  );
}
