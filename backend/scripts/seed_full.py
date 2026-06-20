"""Seed completo de desarrollo: tenant demo + estructura académica + usuarios + RBAC.

Crea todo lo necesario para que la aplicación sea funcional desde el login.
"""
import asyncio
import uuid
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "postgresql+asyncpg://activia:activia@postgres:5432/activia_trace"

# ── Tenant ────────────────────────────────────────────────────────────────────
TENANT_SLUG = "demo"
TENANT_NOMBRE = "Institución Demo"

# ── Carreras ──────────────────────────────────────────────────────────────────
CARRERAS = [
    ("ING-SIS", "Ingeniería en Sistemas"),
    ("LIC-ADM", "Licenciatura en Administración"),
    ("CONT", "Contador Público"),
    ("LIC-MKT", "Licenciatura en Marketing"),
    ("ING-IND", "Ingeniería Industrial"),
]

# ── Materias por carrera ──────────────────────────────────────────────────────
MATERIAS_POR_CARRERA = {
    "ING-SIS": [
        ("MAT-DIS", "Matemática Discreta"),
        ("PROG-I", "Programación I"),
        ("PROG-II", "Programación II"),
        ("BD-I", "Bases de Datos I"),
        ("ING-SW", "Ingeniería de Software"),
        ("REDES", "Redes de Computadoras"),
        ("SO", "Sistemas Operativos"),
        ("ALGO", "Algoritmos y Estructuras de Datos"),
    ],
    "LIC-ADM": [
        ("CONT-I", "Contabilidad I"),
        ("ADM-GEN", "Administración General"),
        ("ECO", "Economía"),
        ("RHHH", "Recursos Humanos"),
        ("COM-ORG", "Comportamiento Organizacional"),
    ],
    "CONT": [
        ("CONT-I", "Contabilidad I"),
        ("CONT-II", "Contabilidad II"),
        ("CONT-III", "Contabilidad III"),
        ("IMP-I", "Impuestos I"),
        ("IMP-II", "Impuestos II"),
        ("AUD", "Auditoría"),
    ],
    "LIC-MKT": [
        ("MKT-I", "Marketing I"),
        ("MKT-DIG", "Marketing Digital"),
        ("PUB", "Publicidad"),
        ("INV-MKT", "Investigación de Mercados"),
        ("COM-V", "Comercialización"),
    ],
    "ING-IND": [
        ("PROD", "Producción"),
        ("LOG", "Logística"),
        ("CAL", "Control de Calidad"),
        ("SEG", "Seguridad Industrial"),
        ("INV-OP", "Investigación Operativa"),
    ],
}

# ── Cohortes ──────────────────────────────────────────────────────────────────
COHORTES = [
    (2025, "2025"),
    (2026, "2026"),
]

# ── Roles de dominio (idéntico a seed_dev.py) ─────────────────────────────────
DOMAIN_ROLES = [
    ("alumno", "Alumno"), ("tutor", "Tutor"), ("profesor", "Profesor"),
    ("coordinador", "Coordinador"), ("nexo", "Nexo"), ("admin", "Administrador"),
    ("finanzas", "Finanzas"),
]

# ── Permisos (idéntico a seed_dev.py) ────────────────────────────────────────
PERMISOS = [
    ("estado:ver_propio", "estado", "ver_propio", ""),
    ("evaluaciones:reservar", "evaluaciones", "reservar", ""),
    ("avisos:confirmar", "avisos", "confirmar", ""),
    ("calificaciones:importar", "calificaciones", "importar", ""),
    ("atrasados:ver", "atrasados", "ver", ""),
    ("atrasados:detectar_sin_corregir", "atrasados", "detectar_sin_corregir", ""),
    ("comunicacion:enviar", "comunicacion", "enviar", ""),
    ("comunicacion:aprobar", "comunicacion", "aprobar", ""),
    ("encuentros:gestionar", "encuentros", "gestionar", ""),
    ("guardias:registrar", "guardias", "registrar", ""),
    ("tareas:gestionar", "tareas", "gestionar", ""),
    ("avisos:publicar", "avisos", "publicar", ""),
    ("equipos:asignar", "equipos", "asignar", ""),
    ("estructura:gestionar", "estructura", "gestionar", ""),
    ("estructura:ver", "estructura", "ver", ""),
    ("usuarios:gestionar", "usuarios", "gestionar", ""),
    ("auditoria:ver", "auditoria", "ver", ""),
    ("grilla:operar", "grilla", "operar", ""),
    ("liquidaciones:calcular", "liquidaciones", "calcular", ""),
    ("liquidaciones:ver", "liquidaciones", "ver", ""),
    ("liquidaciones:cerrar", "liquidaciones", "cerrar", ""),
    ("liquidaciones:exportar", "liquidaciones", "exportar", ""),
    ("facturas:gestionar", "facturas", "gestionar", ""),
    ("coloquios:gestionar", "coloquios", "gestionar", ""),
    ("coloquios:reservar", "coloquios", "reservar", ""),
    ("configuracion:gestionar", "configuracion", "gestionar", ""),
    ("impersonacion:usar", "impersonacion", "usar", ""),
    ("padron:cargar", "padron", "cargar", ""),
    ("padron:vaciar", "padron", "vaciar", ""),
]

MATRIZ = [
    ("alumno", "estado:ver_propio", "propio"),
    ("alumno", "evaluaciones:reservar", "propio"),
    ("alumno", "avisos:confirmar", "global"),
    ("alumno", "coloquios:reservar", "propio"),
    ("tutor", "avisos:confirmar", "global"),
    ("tutor", "atrasados:ver", "global"),
    ("tutor", "atrasados:detectar_sin_corregir", "global"),
    ("tutor", "encuentros:gestionar", "global"),
    ("tutor", "guardias:registrar", "propio"),
    ("profesor", "avisos:confirmar", "global"),
    ("profesor", "calificaciones:importar", "propio"),
    ("profesor", "atrasados:ver", "propio"),
    ("profesor", "atrasados:detectar_sin_corregir", "propio"),
    ("profesor", "comunicacion:enviar", "propio"),
    ("profesor", "encuentros:gestionar", "propio"),
    ("profesor", "guardias:registrar", "propio"),
    ("profesor", "tareas:gestionar", "propio"),
    ("profesor", "padron:cargar", "propio"),
    ("profesor", "padron:vaciar", "propio"),
    ("coordinador", "avisos:confirmar", "global"),
    ("coordinador", "calificaciones:importar", "global"),
    ("coordinador", "atrasados:ver", "global"),
    ("coordinador", "atrasados:detectar_sin_corregir", "global"),
    ("coordinador", "comunicacion:enviar", "global"),
    ("coordinador", "comunicacion:aprobar", "global"),
    ("coordinador", "encuentros:gestionar", "global"),
    ("coordinador", "guardias:registrar", "global"),
    ("coordinador", "tareas:gestionar", "global"),
    ("coordinador", "avisos:publicar", "global"),
    ("coordinador", "equipos:asignar", "global"),
    ("coordinador", "estructura:ver", "global"),
    ("coordinador", "auditoria:ver", "propio"),
    ("coordinador", "padron:cargar", "global"),
    ("coordinador", "padron:vaciar", "global"),
    ("coordinador", "coloquios:gestionar", "global"),
    ("nexo", "avisos:confirmar", "global"),
    ("nexo", "avisos:publicar", "global"),
    ("nexo", "comunicacion:enviar", "global"),
    ("nexo", "atrasados:ver", "global"),
    ("nexo", "tareas:gestionar", "global"),
    ("nexo", "equipos:asignar", "global"),
    ("admin", "avisos:confirmar", "global"),
    ("admin", "calificaciones:importar", "global"),
    ("admin", "atrasados:ver", "global"),
    ("admin", "atrasados:detectar_sin_corregir", "global"),
    ("admin", "comunicacion:enviar", "global"),
    ("admin", "comunicacion:aprobar", "global"),
    ("admin", "encuentros:gestionar", "global"),
    ("admin", "guardias:registrar", "global"),
    ("admin", "tareas:gestionar", "global"),
    ("admin", "avisos:publicar", "global"),
    ("admin", "equipos:asignar", "global"),
    ("admin", "estructura:ver", "global"),
    ("admin", "estructura:gestionar", "global"),
    ("admin", "usuarios:gestionar", "global"),
    ("admin", "coloquios:gestionar", "global"),
    ("admin", "auditoria:ver", "global"),
    ("admin", "configuracion:gestionar", "global"),
    ("admin", "liquidaciones:ver", "global"),
    ("finanzas", "avisos:confirmar", "global"),
    ("finanzas", "auditoria:ver", "global"),
    ("finanzas", "grilla:operar", "global"),
    ("finanzas", "liquidaciones:calcular", "global"),
    ("finanzas", "liquidaciones:ver", "global"),
    ("finanzas", "liquidaciones:cerrar", "global"),
    ("finanzas", "liquidaciones:exportar", "global"),
    ("finanzas", "facturas:gestionar", "global"),
]

# ── Usuarios demo ─────────────────────────────────────────────────────────────
USUARIOS = [
    # (email, password, legajo, nombre, apellido, rol_code)
    ("admin@demo.com", "Admin1234!", "ADMIN-001", "Admin", "Demo", "admin"),
    ("coordinador@demo.com", "Demo1234!", "COORD-001", "Carlos", "Coordinador", "coordinador"),
    ("profesor@demo.com", "Demo1234!", "PROF-001", "María", "Profesora", "profesor"),
    ("tutor@demo.com", "Demo1234!", "TUT-001", "Lucía", "Tutora", "tutor"),
    ("nexo@demo.com", "Demo1234!", "NEX-001", "Pedro", "Nexo", "nexo"),
    ("finanzas@demo.com", "Demo1234!", "FIN-001", "Ana", "Finanzas", "finanzas"),
    ("alumno@demo.com", "Demo1234!", "ALU-001", "Sofía", "Alumna", "alumno"),
]


async def run() -> None:
    from app.core.security import encryption_service, email_lookup_hash, hash_password

    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        # ════════════════════════════════════════════════════════════
        # 1. TENANT
        # ════════════════════════════════════════════════════════════
        r = await conn.execute(
            text("SELECT id FROM tenant WHERE slug = :slug"),
            {"slug": TENANT_SLUG},
        )
        row = r.fetchone()
        if row:
            tid = str(row[0])
            print(f"✅ Tenant existente: {TENANT_SLUG} (id={tid})")
        else:
            tid = str(uuid.uuid4())
            now = datetime.utcnow()
            await conn.execute(
                text(
                    "INSERT INTO tenant (id, slug, nombre, activo, created_at, updated_at) "
                    "VALUES (:id, :slug, :nombre, true, :now, :now)"
                ),
                {"id": tid, "slug": TENANT_SLUG, "nombre": TENANT_NOMBRE, "now": now},
            )
            print(f"✅ Tenant creado: {TENANT_SLUG} (id={tid})")

        # ════════════════════════════════════════════════════════════
        # 2. CARRERAS
        # ════════════════════════════════════════════════════════════
        carrera_ids = {}
        for codigo, nombre in CARRERAS:
            r = await conn.execute(
                text("SELECT id FROM carrera WHERE tenant_id = :tid AND codigo = :codigo"),
                {"tid": tid, "codigo": codigo},
            )
            row = r.fetchone()
            if row:
                carrera_ids[codigo] = str(row[0])
                print(f"  ↳ Carrera existente: {codigo} - {nombre}")
            else:
                cid = str(uuid.uuid4())
                await conn.execute(
                    text(
                        "INSERT INTO carrera (id, tenant_id, codigo, nombre, estado, created_at, updated_at) "
                        "VALUES (:id, :tid, :codigo, :nombre, 'activa', NOW(), NOW())"
                    ),
                    {"id": cid, "tid": tid, "codigo": codigo, "nombre": nombre},
                )
                carrera_ids[codigo] = cid
                print(f"  ✅ Carrera creada: {codigo} - {nombre}")
        print(f"✅ Carreras: {len(CARRERAS)}")

        # ════════════════════════════════════════════════════════════
        # 3. MATERIAS
        # ════════════════════════════════════════════════════════════
        materia_ids = {}
        total_materias = 0
        for carrera_codigo, materias in MATERIAS_POR_CARRERA.items():
            for codigo, nombre in materias:
                r = await conn.execute(
                    text("SELECT id FROM materia WHERE tenant_id = :tid AND codigo = :codigo"),
                    {"tid": tid, "codigo": codigo},
                )
                row = r.fetchone()
                if row:
                    materia_ids[codigo] = str(row[0])
                else:
                    mid = str(uuid.uuid4())
                    await conn.execute(
                        text(
                            "INSERT INTO materia (id, tenant_id, codigo, nombre, estado, created_at, updated_at) "
                            "VALUES (:id, :tid, :codigo, :nombre, 'activa', NOW(), NOW())"
                        ),
                        {"id": mid, "tid": tid, "codigo": codigo, "nombre": nombre},
                    )
                    materia_ids[codigo] = mid
                total_materias += 1
        print(f"✅ Materias: {total_materias}")

        # ════════════════════════════════════════════════════════════
        # 4. COHORTES
        # ════════════════════════════════════════════════════════════
        cohorte_ids = {}
        for carrera_codigo in [c[0] for c in CARRERAS]:
            cid = carrera_ids[carrera_codigo]
            for anio, nombre in COHORTES:
                r = await conn.execute(
                    text(
                        "SELECT co.id FROM cohorte co "
                        "WHERE co.tenant_id = :tid AND co.carrera_id = :carrera_id AND co.nombre = :nombre"
                    ),
                    {"tid": tid, "carrera_id": cid, "nombre": nombre},
                )
                row = r.fetchone()
                key = f"{carrera_codigo}-{anio}"
                if row:
                    cohorte_ids[key] = str(row[0])
                else:
                    cohid = str(uuid.uuid4())
                    await conn.execute(
                        text(
                            "INSERT INTO cohorte (id, tenant_id, carrera_id, nombre, anio, vig_desde, vig_hasta, estado, created_at, updated_at) "
                            "VALUES (:id, :tid, :carrera_id, :nombre, :anio, :vig_desde, NULL, 'activa', NOW(), NOW())"
                        ),
                        {
                            "id": cohid,
                            "tid": tid,
                            "carrera_id": cid,
                            "nombre": nombre,
                            "anio": anio,
                            "vig_desde": f"{anio}-01-01",
                        },
                    )
                    cohorte_ids[key] = cohid
        print(f"✅ Cohortes: {len(CARRERAS) * len(COHORTES)}")

        # ════════════════════════════════════════════════════════════
        # 5. ROLES DEL DOMINIO
        # ════════════════════════════════════════════════════════════
        role_ids = {}
        for code, nombre in DOMAIN_ROLES:
            r = await conn.execute(
                text("SELECT id FROM role WHERE tenant_id = :tid AND code = :code"),
                {"tid": tid, "code": code},
            )
            row = r.fetchone()
            if row:
                role_ids[code] = str(row[0])
            else:
                rid = str(uuid.uuid4())
                await conn.execute(
                    text(
                        "INSERT INTO role (id, tenant_id, code, nombre, created_at, updated_at) "
                        "VALUES (:id, :tid, :code, :nombre, NOW(), NOW())"
                    ),
                    {"id": rid, "tid": tid, "code": code, "nombre": nombre},
                )
                role_ids[code] = rid
        print(f"✅ Roles: {len(DOMAIN_ROLES)}")

        # ════════════════════════════════════════════════════════════
        # 6. PERMISOS
        # ════════════════════════════════════════════════════════════
        permiso_ids = {}
        for code, modulo, accion, _ in PERMISOS:
            r = await conn.execute(
                text("SELECT id FROM permiso WHERE tenant_id = :tid AND code = :code"),
                {"tid": tid, "code": code},
            )
            row = r.fetchone()
            if row:
                permiso_ids[code] = str(row[0])
            else:
                pid = str(uuid.uuid4())
                await conn.execute(
                    text(
                        "INSERT INTO permiso (id, tenant_id, modulo, accion, code, created_at, updated_at) "
                        "VALUES (:id, :tid, :modulo, :accion, :code, NOW(), NOW())"
                    ),
                    {"id": pid, "tid": tid, "modulo": modulo, "accion": accion, "code": code},
                )
                permiso_ids[code] = pid
        print(f"✅ Permisos: {len(PERMISOS)}")

        # ════════════════════════════════════════════════════════════
        # 7. MATRIZ ROL-PERMISO
        # ════════════════════════════════════════════════════════════
        count_matriz = 0
        for rc, pc, scope in MATRIZ:
            await conn.execute(
                text(
                    "INSERT INTO rol_permiso (tenant_id, role_id, permiso_id, scope, created_at) "
                    "SELECT :tid, :rid, :pid, :scope, NOW() "
                    "WHERE NOT EXISTS ("
                    "  SELECT 1 FROM rol_permiso rp "
                    "  WHERE rp.tenant_id = :tid2 AND rp.role_id = :rid2 AND rp.permiso_id = :pid2"
                    ")"
                ),
                {
                    "tid": tid, "rid": role_ids[rc], "pid": permiso_ids[pc],
                    "tid2": tid, "rid2": role_ids[rc], "pid2": permiso_ids[pc],
                    "scope": scope,
                },
            )
            count_matriz += 1
        print(f"✅ Matriz rol-permiso: {count_matriz} entradas")

        # ════════════════════════════════════════════════════════════
        # 8. USUARIOS DEMO
        # ════════════════════════════════════════════════════════════
        created_users = []
        for email, password, legajo, nombre, apellido, rol_code in USUARIOS:
            email_lookup = email_lookup_hash(email)
            r = await conn.execute(
                text("SELECT id FROM \"user\" WHERE tenant_id = :tid AND email_lookup = :el"),
                {"tid": tid, "el": email_lookup},
            )
            row = r.fetchone()
            if row:
                uid = str(row[0])
                print(f"  ↳ Usuario existente: {email}")
            else:
                uid = str(uuid.uuid4())
                await conn.execute(
                    text(
                        "INSERT INTO \"user\" (id, tenant_id, email_encrypted, email_lookup, password_hash, "
                        "legajo, is_active, totp_enabled, nombre, apellidos, created_at, updated_at) "
                        "VALUES (:id, :tid, :ee, :el, :ph, :legajo, true, false, :nombre, :apellido, NOW(), NOW())"
                    ),
                    {
                        "id": uid, "tid": tid,
                        "ee": encryption_service.encrypt(email),
                        "el": email_lookup,
                        "ph": hash_password(password),
                        "legajo": legajo,
                        "nombre": nombre,
                        "apellido": apellido,
                    },
                )
                print(f"  ✅ Usuario creado: {email} / {password}")
                created_users.append((uid, email))

            # Asignar rol al usuario
            if rol_code in role_ids:
                await conn.execute(
                    text(
                        "INSERT INTO user_role (user_id, role_id, tenant_id) "
                        "SELECT :uid, :rid, :tid WHERE NOT EXISTS ("
                        "  SELECT 1 FROM user_role "
                        "  WHERE user_id = :uid2 AND role_id = :rid2 AND tenant_id = :tid2"
                        ")"
                    ),
                    {
                        "uid": uid, "rid": role_ids[rol_code], "tid": tid,
                        "uid2": uid, "rid2": role_ids[rol_code], "tid2": tid,
                    },
                )

        print(f"✅ Usuarios: {len(USUARIOS)} procesados")

        # ════════════════════════════════════════════════════════════
        # COMMIT
        # ════════════════════════════════════════════════════════════
        await conn.commit()

    await engine.dispose()
    print("")
    print("╔══════════════════════════════════════════════════╗")
    print("║       🌱 SEED COMPLETO                          ║")
    print("╠══════════════════════════════════════════════════╣")
    print(f"║  Tenant:    {TENANT_SLUG} ({TENANT_NOMBRE})")
    print(f"║  Carreras:  {len(CARRERAS)}")
    print(f"║  Materias:  {total_materias}")
    print(f"║  Cohortes:  {len(CARRERAS) * len(COHORTES)}")
    print(f"║  Roles:     {len(DOMAIN_ROLES)}")
    print(f"║  Permisos:  {len(PERMISOS)}")
    print(f"║  Usuarios:  {len(USUARIOS)}")
    print("╠══════════════════════════════════════════════════╣")
    print("║  USUARIOS DEMO:                                 ║")
    print("║  admin@demo.com     / Admin1234!   (admin)      ║")
    print("║  coordinador@demo   / Demo1234!    (coordinador)║")
    print("║  profesor@demo.com  / Demo1234!    (profesor)   ║")
    print("║  tutor@demo.com     / Demo1234!    (tutor)      ║")
    print("║  nexo@demo.com      / Demo1234!    (nexo)       ║")
    print("║  finanzas@demo.com  / Demo1234!    (finanzas)   ║")
    print("║  alumno@demo.com    / Demo1234!    (alumno)     ║")
    print("╚══════════════════════════════════════════════════╝")


if __name__ == "__main__":
    asyncio.run(run())
