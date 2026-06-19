# Tasks: C-17 — Programas y Fechas Académicas

## 1. Verificación de código existente

- [ ] 1.1 Verificar que la migración `601bb609ae5b_006_programas_y_fechas_academicas.py` existe y su `down_revision` apunta a `005_estructura_academica`
- [ ] 1.2 Verificar que los routers `programas.py` y `fechas_academicas.py` están importados y registrados en `app/main.py`
- [ ] 1.3 Verificar que los modelos `ProgramaMateria` y `FechaAcademica` importan correctamente sus dependencias (TenantScopedMixin, FK a materia/carrera/cohorte)
- [ ] 1.4 Ejecutar `pytest --collect-only` para verificar que todos los tests existentes se recolectan sin errores de importación

## 2. Tests de modelo y schema (ProgramaMateria)

- [ ] 2.1 Confirmar que `test_model_programa_materia.py` cubre: persistencia, FK violation, unique constraint con distintas combinaciones
- [ ] 2.2 Confirmar que `test_schemas_programa_materia.py` cubre: create válido, extra field rejected, referencia_archivo opcional, referencia_archivo opaco, update válido, partial update, empty update, response from_attributes

## 3. Tests de modelo y schema (FechaAcademica)

- [ ] 3.1 Confirmar que `test_model_fecha_academica.py` cubre: persistencia, unique constraint mismo tipo+numero, mismo tipo distinto numero OK
- [ ] 3.2 Confirmar que `test_schemas_fecha_academica.py` cubre: create válido, tipo fuera del enum rejected, numero cero/negativo rejected, todos los enum válidos aceptados, extra field rejected, update parcial/vacío, CalendarioPeriodo

## 4. Tests de repositorio — ProgramaMateria

- [ ] 4.1 Confirmar que `test_repositories_programa_materia.py` cubre: create + get_by_id, aislamiento por tenant en get, list con filtros, get_by_combination, soft_delete excluye del listado, aislamiento por tenant en list
- [ ] 4.2 Agregar test faltante: `test_soft_delete_not_found_returns_false` — soft_delete con ID inexistente retorna `False`
- [ ] 4.3 Agregar test faltante: `test_tenant_isolation_across_operations` — datos de otro tenant no interfieren con create/list/get

## 5. Tests de repositorio — FechaAcademica

- [ ] 5.1 Confirmar que `test_repositories_fecha_academica.py` cubre: create + get_by_id, aislamiento por tenant, list ordenado por fecha, list con filtros, get_by_instance, soft_delete, tenant isolation
- [ ] 5.2 Agregar test faltante: `test_list_filters_by_periodo` — filtrar por periodo string exacto
- [ ] 5.3 Agregar test faltante: `test_soft_delete_not_found_returns_false` — soft_delete con ID inexistente retorna `False`

## 6. Tests de servicio — ProgramaMateria

- [ ] 6.1 Confirmar que `test_services_programa_materia.py` cubre: create éxito, create duplicado 409, create materia not found 404, get éxito, get not found 404, update éxito, soft_delete éxito, list con filtros
- [ ] 6.2 Agregar test faltante: `test_create_carrera_not_found_fails` — carrera inexistente devuelve 404
- [ ] 6.3 Agregar test faltante: `test_create_cohorte_not_found_fails` — cohorte inexistente devuelve 404
- [ ] 6.4 Agregar test faltante: `test_create_sin_referencia_archivo` — crear programa sin referencia_archivo (campo opcional, queda None)
- [ ] 6.5 Agregar test faltante: `test_update_referencia_archivo` — actualizar referencia_archivo de null a valor y viceversa

## 7. Tests de servicio — FechaAcademica

- [ ] 7.1 Confirmar que `test_services_fecha_academica.py` cubre: create éxito, create duplicado 409, create materia not found 404, update éxito, soft_delete éxito, list_tabular ordenado, list_calendario agrupado por periodo, build_lms_fragment con fechas, build_lms_fragment vacío, build_lms_fragment single
- [ ] 7.2 Agregar test faltante: `test_create_cohorte_not_found_fails` — cohorte inexistente devuelve 404
- [ ] 7.3 Agregar test faltante: `test_create_invalid_tipo_fails` — tipo inválido devuelve 422
- [ ] 7.4 Agregar test faltante: `test_update_not_found_fails` — actualizar fecha inexistente devuelve 404
- [ ] 7.5 Agregar test faltante: `test_delete_not_found_fails` — eliminar fecha inexistente devuelve False/404

## 8. Tests de endpoint — ProgramaMateria (fixture `client` con DB real)

- [ ] 8.1 Confirmar que `test_programas_endpoints.py` cubre: 401 sin token, 403 sin permiso create, 403 sin permiso list, 422 extra field
- [ ] 8.2 Agregar test: `test_create_happy_path_201` — crear programa válido con DB real, verificar 201 + body con id/timestamps
- [ ] 8.3 Agregar test: `test_create_duplicate_409` — misma combinación devuelve 409
- [ ] 8.4 Agregar test: `test_list_happy_path_200` — listar devuelve 200 con array
- [ ] 8.5 Agregar test: `test_get_by_id_200` — obtener por ID devuelve 200
- [ ] 8.6 Agregar test: `test_get_by_id_404` — ID inexistente devuelve 404
- [ ] 8.7 Agregar test: `test_update_200` — actualizar título devuelve 200 con datos nuevos
- [ ] 8.8 Agregar test: `test_soft_delete_204` — eliminar devuelve 204 y no aparece en get posterior
- [ ] 8.9 Agregar test: `test_delete_not_found_404` — eliminar ID inexistente devuelve 404
- [ ] 8.10 Agregar test: `test_list_filter_by_materia` — filtrar por materia_id devuelve solo esa materia

## 9. Tests de endpoint — FechaAcademica (fixture `client` con DB real)

- [ ] 9.1 Confirmar que `test_fechas_academicas_endpoints.py` cubre: 401 sin token, 403 sin permiso create, 422 tipo fuera del enum, 422 extra field, 403 sin permiso list, 401 en calendario, 422 numero negativo
- [ ] 9.2 Agregar test: `test_create_happy_path_201` — crear fecha válida, verificar 201 + body
- [ ] 9.3 Agregar test: `test_create_duplicate_409` — mismo tipo+numero devuelve 409
- [ ] 9.4 Agregar test: `test_list_happy_path_200` — listar devuelve 200 con array ordenado
- [ ] 9.5 Agregar test: `test_get_by_id_200` — obtener por ID devuelve 200
- [ ] 9.6 Agregar test: `test_get_by_id_404` — ID inexistente devuelve 404
- [ ] 9.7 Agregar test: `test_update_200` — actualizar titulo devuelve 200
- [ ] 9.8 Agregar test: `test_soft_delete_204` — eliminar devuelve 204
- [ ] 9.9 Agregar test: `test_delete_not_found_404` — eliminar ID inexistente devuelve 404
- [ ] 9.10 Agregar test: `test_list_filter_by_tipo` — filtrar por tipo devuelve solo ese tipo
- [ ] 9.11 Agregar test: `test_calendario_endpoint_200` — endpoint /calendario devuelve agrupado por periodo
- [ ] 9.12 Agregar test: `test_lms_fragment_endpoint_200` — endpoint /lms-fragment devuelve fragmento con fechas
- [ ] 9.13 Agregar test: `test_lms_fragment_missing_params_422` — endpoint /lms-fragment sin materia_id devuelve 422
- [ ] 9.14 Agregar test: `test_lms_fragment_empty_200` — endpoint /lms-fragment sin fechas devuelve "Sin evaluaciones registradas"

## 10. Correr validación final

- [ ] 10.1 Ejecutar `pytest -v -x --run-db` y verificar que todos los tests pasan en verde
- [ ] 10.2 Verificar cobertura ≥80% líneas y ≥90% reglas de negocio para los módulos nuevos
- [ ] 10.3 Verificar que ningún archivo excede 500 LOC en backend
