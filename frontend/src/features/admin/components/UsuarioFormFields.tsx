// ── UsuarioFormFields ──────────────────────────────────────────────────────
// Reusable field sub-components and Zod schema for UsuarioFormDialog.
// Extracted to keep UsuarioFormDialog under 200 LOC.

import { useState } from 'react';
import { z } from 'zod';
import type { UseFormRegister, FieldErrors } from 'react-hook-form';
import type { UsuarioFormData } from '@/features/admin/types';

export const REGIONALES = ['GBA', 'Capital', 'Interior', 'Online'];

export const usuarioSchema = z.object({
  legajo: z.string().min(1, 'El legajo es requerido'),
  nombre: z.string().min(1, 'El nombre es requerido'),
  apellidos: z.string().min(1, 'Los apellidos son requeridos'),
  email: z.string().email('Email inválido'),
  regional: z.string().min(1, 'La regional es requerida'),
  facturador: z.boolean(),
  dni: z.string().min(1, 'El DNI es requerido'),
  cuil: z.string().min(1, 'El CUIL es requerido'),
  cbu: z.string().optional(),
  alias_cbu: z.string().optional(),
  password: z.string().optional(),
});

function EyeIcon({ visible }: { visible: boolean }) {
  if (visible) {
    return (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
      </svg>
    );
  }
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
  );
}

interface MaskedInputProps {
  label: string;
  fieldName: keyof UsuarioFormData;
  register: UseFormRegister<UsuarioFormData>;
  error?: string;
}

export function MaskedInput({ label, fieldName, register, error }: MaskedInputProps) {
  const [visible, setVisible] = useState(false);
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700">{label}</label>
      <div className="relative mt-1">
        <input
          {...register(fieldName)}
          type={visible ? 'text' : 'password'}
          autoComplete="off"
          className="block w-full rounded-md border border-gray-300 px-3 py-2 pr-9 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          className="absolute inset-y-0 right-2 flex items-center text-gray-400 hover:text-gray-600"
          aria-label={visible ? 'Ocultar' : 'Mostrar'}
        >
          <EyeIcon visible={visible} />
        </button>
      </div>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  );
}

interface BaseFieldsProps {
  register: UseFormRegister<UsuarioFormData>;
  errors: FieldErrors<UsuarioFormData>;
}

export function UsuarioBaseFields({ register, errors }: BaseFieldsProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <div>
        <label className="block text-sm font-medium text-gray-700">Legajo</label>
        <input
          {...register('legajo')}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
        {errors.legajo && <p className="mt-1 text-xs text-red-600">{errors.legajo.message}</p>}
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700">Regional</label>
        <select
          {...register('regional')}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="">Seleccionar…</option>
          {REGIONALES.map((r) => <option key={r} value={r}>{r}</option>)}
        </select>
        {errors.regional && <p className="mt-1 text-xs text-red-600">{errors.regional.message}</p>}
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700">Nombre</label>
        <input
          {...register('nombre')}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
        {errors.nombre && <p className="mt-1 text-xs text-red-600">{errors.nombre.message}</p>}
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700">Apellidos</label>
        <input
          {...register('apellidos')}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
        {errors.apellidos && <p className="mt-1 text-xs text-red-600">{errors.apellidos.message}</p>}
      </div>
      <div className="sm:col-span-2">
        <label className="block text-sm font-medium text-gray-700">Email</label>
        <input
          {...register('email')}
          type="email"
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
        {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>}
      </div>
      <div className="sm:col-span-2 flex items-center gap-2">
        <input
          {...register('facturador')}
          type="checkbox"
          id="facturador"
          className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
        />
        <label htmlFor="facturador" className="text-sm text-gray-700">Facturador</label>
      </div>
    </div>
  );
}
