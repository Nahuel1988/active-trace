import PadronPage from '@/features/padron/pages/ImportPadronPage';
import CalificacionesPage from '@/features/calificaciones/pages/ImportCalificacionesPage';

export default function ImportPage() {
  return (
    <div className="space-y-12">
      <section>
        <PadronPage />
      </section>
      <hr className="border-gray-200" />
      <section>
        <CalificacionesPage />
      </section>
    </div>
  );
}
