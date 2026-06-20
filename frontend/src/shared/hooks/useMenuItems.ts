// ── useMenuItems ──────────────────────────────────────────────────────────────
// Custom hook que resuelve los items navegables del sidebar según permisos.
// D-02: Filtrado fuera del render, usePermission llamado en posiciones fijas.
// Sin hooks violation.

import { usePermission } from '@/shared/hooks/usePermission';

export interface SidebarItem {
  label: string;
  path: string;
  /** Ícono SVG inline opcional */
  icon?: string;
  /** Permiso requerido (opcional). Si no se especifica, visible para todos */
  permission?: string;
}

const sidebarItems: SidebarItem[] = [
  {
    label: 'Inicio',
    path: '/',
    icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
  },
  {
    label: 'Equipos docentes',
    path: '/equipos',
    permission: 'equipos:asignar',
  },
  {
    label: 'Avisos',
    path: '/avisos',
    permission: 'avisos:publicar',
  },
  {
    label: 'Tareas',
    path: '/tareas',
    permission: 'tareas:gestionar',
  },
  {
    label: 'Coloquios',
    path: '/coloquios',
    permission: 'coloquios:gestionar',
  },
  {
    label: 'Estructura',
    path: '/estructura',
    permission: 'estructura:gestionar',
  },
  {
    label: 'Encuentros',
    path: '/encuentros',
    permission: 'encuentros:gestionar',
  },
  {
    label: 'Guardias',
    path: '/guardias',
    permission: 'guardias:registrar',
  },
  {
    label: 'Importar padrón/calificaciones',
    path: '/importar',
    permission: 'calificaciones:importar',
  },
  {
    label: 'Atrasados',
    path: '/atrasados',
    permission: 'atrasados:ver',
  },
  {
    label: 'Comunicaciones',
    path: '/comunicaciones',
    permission: 'comunicacion:enviar',
  },
  {
    label: 'Finanzas',
    path: '/finanzas',
    permission: 'liquidaciones:ver',
  },
  {
    label: 'Usuarios',
    path: '/admin/usuarios',
    permission: 'usuarios:gestionar',
  },
  {
    label: 'Auditoría',
    path: '/admin/auditoria',
    permission: 'auditoria:ver',
  },
];

export { sidebarItems };

export function useMenuItems(): SidebarItem[] {
  // Llamar usePermission en posiciones fijas (top-level del hook)
  const canEquipos = usePermission('equipos:asignar');
  const canAvisos = usePermission('avisos:publicar');
  const canTareas = usePermission('tareas:gestionar');
  const canColoquios = usePermission('coloquios:gestionar');
  const canEstructura = usePermission('estructura:gestionar');
  const canEncuentros = usePermission('encuentros:gestionar');
  const canGuardias = usePermission('guardias:registrar');
  const canImportar = usePermission('calificaciones:importar');
  const canAtrasados = usePermission('atrasados:ver');
  const canComunicaciones = usePermission('comunicacion:enviar');
  const canFinanzas = usePermission('liquidaciones:ver');
  const canUsuarios = usePermission('usuarios:gestionar');
  const canAuditoria = usePermission('auditoria:ver');

  const permMap: Record<string, boolean> = {
    'equipos:asignar': canEquipos,
    'avisos:publicar': canAvisos,
    'tareas:gestionar': canTareas,
    'coloquios:gestionar': canColoquios,
    'estructura:gestionar': canEstructura,
    'encuentros:gestionar': canEncuentros,
    'guardias:registrar': canGuardias,
    'calificaciones:importar': canImportar,
    'atrasados:ver': canAtrasados,
    'comunicacion:enviar': canComunicaciones,
    'liquidaciones:ver': canFinanzas,
    'usuarios:gestionar': canUsuarios,
    'auditoria:ver': canAuditoria,
  };

  return sidebarItems.filter((item) => {
    if (!item.permission) return true;
    return permMap[item.permission] ?? false;
  });
}
