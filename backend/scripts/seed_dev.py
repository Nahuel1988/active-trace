"""Seed de desarrollo: tenant demo + usuario admin + RBAC completo."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://activia:activia@postgres:5432/activia_trace"

DOMAIN_ROLES = [
    ("alumno", "Alumno"), ("tutor", "Tutor"), ("profesor", "Profesor"),
    ("coordinador", "Coordinador"), ("nexo", "Nexo"), ("admin", "Administrador"),
    ("finanzas", "Finanzas"),
]

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


async def run() -> None:
    from app.core.security import encryption_service, email_lookup_hash, hash_password

    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        r = await conn.execute(text("SELECT id FROM tenant LIMIT 1"))
        row = r.fetchone()
        if not row:
            print("No hay tenant — creá uno primero")
            return
        tid = str(row.id)
        print(f"Tenant: {tid}")

        for code, nombre in DOMAIN_ROLES:
            await conn.execute(text(
                "INSERT INTO role (id,tenant_id,code,nombre,created_at,updated_at) "
                "SELECT gen_random_uuid(),:tid,:code,:nombre,NOW(),NOW() "
                "WHERE NOT EXISTS (SELECT 1 FROM role WHERE tenant_id=:tid2 AND code=:c2)"
            ), {"tid": tid, "code": code, "nombre": nombre, "tid2": tid, "c2": code})
        print("Roles OK")

        for code, modulo, accion, _ in PERMISOS:
            await conn.execute(text(
                "INSERT INTO permiso (id,tenant_id,modulo,accion,code,created_at,updated_at) "
                "SELECT gen_random_uuid(),:tid,:m,:a,:code,NOW(),NOW() "
                "WHERE NOT EXISTS (SELECT 1 FROM permiso WHERE tenant_id=:tid2 AND code=:c2)"
            ), {"tid": tid, "m": modulo, "a": accion, "code": code, "tid2": tid, "c2": code})
        print("Permisos OK")

        for rc, pc, scope in MATRIZ:
            await conn.execute(text(
                "INSERT INTO rol_permiso (tenant_id,role_id,permiso_id,scope,created_at) "
                "SELECT :tid,r.id,p.id,:scope,NOW() "
                "FROM role r CROSS JOIN permiso p "
                "WHERE r.tenant_id=:tid2 AND r.code=:rc AND p.tenant_id=:tid3 AND p.code=:pc "
                "AND NOT EXISTS (SELECT 1 FROM rol_permiso rp WHERE rp.tenant_id=:tid4 AND rp.role_id=r.id AND rp.permiso_id=p.id)"
            ), {"tid": tid, "scope": scope, "tid2": tid, "rc": rc, "tid3": tid, "pc": pc, "tid4": tid})
        print("Matriz OK")

        r = await conn.execute(text("SELECT id FROM role WHERE tenant_id=:tid AND code='admin'"), {"tid": tid})
        admin_role = r.fetchone()
        r = await conn.execute(text('SELECT id FROM "user" WHERE tenant_id=:tid LIMIT 1'), {"tid": tid})
        user = r.fetchone()
        if not user:
            uid_str = __import__("uuid").uuid4().__str__()
            email = "admin@demo.com"
            pwd = "Admin1234!"
            await conn.execute(text(
                'INSERT INTO "user" (id,tenant_id,email_encrypted,email_lookup,password_hash,legajo,is_active,totp_enabled) '
                "VALUES (:id,:tid,:ee,:el,:ph,'ADMIN-001',true,false)"
            ), {"id": uid_str, "tid": tid, "ee": encryption_service.encrypt(email), "el": email_lookup_hash(email), "ph": hash_password(pwd)})
            user_id = uid_str
            print(f"Usuario creado: {email} / {pwd}")
        else:
            user_id = str(user.id)
            print("Usuario ya existe")

        if admin_role:
            rid = str(admin_role.id)
            await conn.execute(text(
                "INSERT INTO user_role (user_id,role_id,tenant_id) "
                "SELECT :uid,:rid,:tid WHERE NOT EXISTS "
                "(SELECT 1 FROM user_role WHERE user_id=:uid2 AND role_id=:rid2 AND tenant_id=:tid2)"
            ), {"uid": user_id, "rid": rid, "tid": tid, "uid2": user_id, "rid2": rid, "tid2": tid})
            print("Rol admin asignado")

        await conn.commit()
    await engine.dispose()
    print("Seed completo!")


if __name__ == "__main__":
    asyncio.run(run())
