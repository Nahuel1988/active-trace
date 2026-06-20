import { useState } from 'react';

interface ComentarioFormProps {
  onEnviar: (contenido: string) => void;
  isPending: boolean;
}

export function ComentarioForm({ onEnviar, isPending }: ComentarioFormProps) {
  const [contenido, setContenido] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!contenido.trim()) return;
    onEnviar(contenido.trim());
    setContenido('');
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-3">
      <input
        type="text"
        value={contenido}
        onChange={(e) => setContenido(e.target.value)}
        placeholder="Escribí un comentario..."
        className="block flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
      />
      <button
        type="submit"
        disabled={isPending || !contenido.trim()}
        className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isPending ? 'Enviando...' : 'Enviar'}
      </button>
    </form>
  );
}
