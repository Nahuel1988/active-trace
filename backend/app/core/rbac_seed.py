"""Catálogo de permisos y matriz base del dominio.

Derivado 1:1 de ``knowledge-base/03_actores_y_roles.md §3.3``.

Estructuras de datos usadas por la migración 003 para sembrar el
catálogo de permisos y la matriz rol × permiso de cada tenant.

Uso::

    from app.core.rbac_seed import MATRIZ_BASE, PERMISOS

    for permiso_data in PERMISOS:
        ...

    for role_code, permiso_code, scope in MATRIZ_BASE:
        ...
"""

# ---------------------------------------------------------------------------
# Catálogo completo de permisos del dominio
# ---------------------------------------------------------------------------
# Cada entrada: (code, modulo, accion, descripcion)
# code = "{modulo}:{accion}" — unique por tenant
# ---------------------------------------------------------------------------

PERMISOS: list[tuple[str, str, str, str]] = [
    # Estado académico
    (
        "estado:ver_propio",
        "estado",
        "ver_propio",
        "Ver estado académico propio",
    ),
    # Evaluaciones
    (
        "evaluaciones:reservar",
        "evaluaciones",
        "reservar",
        "Reservar instancia de evaluación",
    ),
    # Avisos
    (
        "avisos:confirmar",
        "avisos",
        "confirmar",
        "Confirmar avisos (acknowledgment)",
    ),
    # Calificaciones
    (
        "calificaciones:importar",
        "calificaciones",
        "importar",
        "Importar calificaciones",
    ),
    # Atrasados
    (
        "atrasados:ver",
        "atrasados",
        "ver",
        "Ver alumnos atrasados",
    ),
    (
        "atrasados:detectar_sin_corregir",
        "atrasados",
        "detectar_sin_corregir",
        "Detectar entregas sin corregir",
    ),
    # Comunicación
    (
        "comunicacion:enviar",
        "comunicacion",
        "enviar",
        "Enviar comunicaciones a alumnos",
    ),
    (
        "comunicacion:aprobar",
        "comunicacion",
        "aprobar",
        "Aprobar comunicaciones masivas",
    ),
    # Encuentros
    (
        "encuentros:gestionar",
        "encuentros",
        "gestionar",
        "Gestionar encuentros",
    ),
    # Guardias
    (
        "guardias:registrar",
        "guardias",
        "registrar",
        "Registrar guardias",
    ),
    # Tareas internas
    (
        "tareas:gestionar",
        "tareas",
        "gestionar",
        "Gestionar tareas internas",
    ),
    # Avisos (publicación)
    (
        "avisos:publicar",
        "avisos",
        "publicar",
        "Publicar avisos",
    ),
    # Equipos docentes
    (
        "equipos:asignar",
        "equipos",
        "asignar",
        "Gestionar equipos docentes (asignaciones)",
    ),
    # Estructura académica
    (
        "estructura:ver",
        "estructura",
        "ver",
        "Ver estructura académica (carreras, cohortes, materias, programas, fechas)",
    ),
    (
        "estructura:gestionar",
        "estructura",
        "gestionar",
        "Gestionar estructura académica (carreras, cohortes, materias, programas, fechas)",
    ),
    # Usuarios
    (
        "usuarios:gestionar",
        "usuarios",
        "gestionar",
        "Gestionar usuarios del tenant",
    ),
    # Auditoría
    (
        "auditoria:ver",
        "auditoria",
        "ver",
        "Ver auditoría",
    ),
    # Grilla salarial
    (
        "grilla:operar",
        "grilla",
        "operar",
        "Operar grilla salarial",
    ),
    # Liquidaciones
    (
        "liquidaciones:calcular",
        "liquidaciones",
        "calcular",
        "Calcular liquidaciones",
    ),
    (
        "liquidaciones:cerrar",
        "liquidaciones",
        "cerrar",
        "Cerrar liquidaciones",
    ),
    # Facturas
    (
        "facturas:gestionar",
        "facturas",
        "gestionar",
        "Gestionar facturas",
    ),
    # Configuración del tenant
    (
        "configuracion:gestionar",
        "configuracion",
        "gestionar",
        "Configurar el tenant",
    ),
    # Impersonación (capacidad transversal, flujo en change posterior)
    (
        "impersonacion:usar",
        "impersonacion",
        "usar",
        "Impersonar a otro usuario (suplantación legítima)",
    ),
]

# ---------------------------------------------------------------------------
# Diccionario de códigos para acceso rápido
# ---------------------------------------------------------------------------
CODIGOS_PERMISOS: dict[str, str] = {code: code for code, *_ in PERMISOS}

# ---------------------------------------------------------------------------
# Matriz base del dominio (rol → permiso → scope)
# ---------------------------------------------------------------------------
# Cada entrada: (role_code, permiso_code, scope)
#   scope = "global" | "propio"
# Solo se listan las celdas ✅ o (propio) — las celdas — no generan fila.
# ---------------------------------------------------------------------------

#: Mapeo de nombres de rol en la KB a codes usados en DB
ROLE_ALUMNO = "alumno"
ROLE_TUTOR = "tutor"
ROLE_PROFESOR = "profesor"
ROLE_COORDINADOR = "coordinador"
ROLE_NEXO = "nexo"
ROLE_ADMIN = "admin"
ROLE_FINANZAS = "finanzas"

MATRIZ_BASE: list[tuple[str, str, str]] = [
    # -- ALUMNO --
    (ROLE_ALUMNO, "estado:ver_propio", "propio"),
    (ROLE_ALUMNO, "evaluaciones:reservar", "propio"),
    (ROLE_ALUMNO, "avisos:confirmar", "global"),
    # -- TUTOR --
    (ROLE_TUTOR, "avisos:confirmar", "global"),
    (ROLE_TUTOR, "atrasados:ver", "global"),
    (ROLE_TUTOR, "atrasados:detectar_sin_corregir", "global"),
    (ROLE_TUTOR, "encuentros:gestionar", "global"),
    (ROLE_TUTOR, "guardias:registrar", "propio"),
    # -- PROFESOR --
    (ROLE_PROFESOR, "avisos:confirmar", "global"),
    (ROLE_PROFESOR, "calificaciones:importar", "propio"),
    (ROLE_PROFESOR, "atrasados:ver", "propio"),
    (ROLE_PROFESOR, "atrasados:detectar_sin_corregir", "propio"),
    (ROLE_PROFESOR, "comunicacion:enviar", "propio"),
    (ROLE_PROFESOR, "encuentros:gestionar", "propio"),
    (ROLE_PROFESOR, "guardias:registrar", "propio"),
    (ROLE_PROFESOR, "tareas:gestionar", "propio"),
    # -- COORDINADOR --
    (ROLE_COORDINADOR, "avisos:confirmar", "global"),
    (ROLE_COORDINADOR, "calificaciones:importar", "global"),
    (ROLE_COORDINADOR, "atrasados:ver", "global"),
    (ROLE_COORDINADOR, "atrasados:detectar_sin_corregir", "global"),
    (ROLE_COORDINADOR, "comunicacion:enviar", "global"),
    (ROLE_COORDINADOR, "comunicacion:aprobar", "global"),
    (ROLE_COORDINADOR, "encuentros:gestionar", "global"),
    (ROLE_COORDINADOR, "guardias:registrar", "global"),
    (ROLE_COORDINADOR, "tareas:gestionar", "global"),
    (ROLE_COORDINADOR, "avisos:publicar", "global"),
    (ROLE_COORDINADOR, "equipos:asignar", "global"),
    (ROLE_COORDINADOR, "estructura:ver", "global"),
    (ROLE_COORDINADOR, "auditoria:ver", "propio"),
    # -- NEXO (enlace transversal institución ↔ docentes/alumnos) --
    (ROLE_NEXO, "avisos:confirmar", "global"),
    (ROLE_NEXO, "avisos:publicar", "global"),
    (ROLE_NEXO, "comunicacion:enviar", "global"),
    (ROLE_NEXO, "atrasados:ver", "global"),
    (ROLE_NEXO, "tareas:gestionar", "global"),
    (ROLE_NEXO, "equipos:asignar", "global"),
    # -- ADMIN --
    (ROLE_ADMIN, "avisos:confirmar", "global"),
    (ROLE_ADMIN, "calificaciones:importar", "global"),
    (ROLE_ADMIN, "atrasados:ver", "global"),
    (ROLE_ADMIN, "atrasados:detectar_sin_corregir", "global"),
    (ROLE_ADMIN, "comunicacion:enviar", "global"),
    (ROLE_ADMIN, "comunicacion:aprobar", "global"),
    (ROLE_ADMIN, "encuentros:gestionar", "global"),
    (ROLE_ADMIN, "guardias:registrar", "global"),
    (ROLE_ADMIN, "tareas:gestionar", "global"),
    (ROLE_ADMIN, "avisos:publicar", "global"),
    (ROLE_ADMIN, "equipos:asignar", "global"),
    (ROLE_ADMIN, "estructura:ver", "global"),
    (ROLE_ADMIN, "estructura:gestionar", "global"),
    (ROLE_ADMIN, "usuarios:gestionar", "global"),
    (ROLE_ADMIN, "auditoria:ver", "global"),
    (ROLE_ADMIN, "configuracion:gestionar", "global"),
    # -- FINANZAS --
    (ROLE_FINANZAS, "avisos:confirmar", "global"),
    (ROLE_FINANZAS, "auditoria:ver", "global"),
    (ROLE_FINANZAS, "grilla:operar", "global"),
    (ROLE_FINANZAS, "liquidaciones:calcular", "global"),
    (ROLE_FINANZAS, "liquidaciones:cerrar", "global"),
    (ROLE_FINANZAS, "facturas:gestionar", "global"),
]

# ---------------------------------------------------------------------------
# Validación: todo permiso en la matriz debe existir en el catálogo
# ---------------------------------------------------------------------------
_CODES_EN_CATALOGO = {code for code, *_ in PERMISOS}
for role_code, permiso_code, scope in MATRIZ_BASE:
    if permiso_code not in _CODES_EN_CATALOGO:
        msg = (
            f"Matriz refiere permiso '{permiso_code}' para rol '{role_code}', "
            f"pero no está en el catálogo PERMISOS"
        )
        raise ValueError(msg)
