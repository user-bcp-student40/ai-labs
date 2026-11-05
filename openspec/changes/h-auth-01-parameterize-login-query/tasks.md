# Tasks

Issue: [#22](https://github.com/user-bcp-student40/ai-labs/issues/22) (H-AUTH-01). Alcance: solo `auth/`. Las pruebas se ejecutan desde `auth/`; Git y OpenSpec, desde la raíz de `ai-labs`. Rama actual `feature/h-auth-01`, sin push durante el Día 1.

## 1. Pruebas de caracterización (antes del cambio funcional)

- [x] 1.1 En `AuthResourceTest`, reforzar la prueba de login válido para comprobar también `expiresIn`, `user.displayName` y `user.role`; verificar que `mvn test` desde `auth/` pasa contra el código actual.
- [x] 1.2 Agregar pruebas de `401` sin `token` para contraseña incorrecta de `student`, usuario inexistente y variantes de capitalización de usuario y contraseña; verificar que pasan contra el código actual.
- [x] 1.3 Agregar pruebas de `400` sin `token` para `username` vacío o en blanco y para `password` ausente; verificar que pasan contra el código actual.
- [x] 1.4 Agregar la prueba de `401` sin `token` para un `username` con comilla simple que no existe; verificar que pasa contra el código actual y no fijar el texto del mensaje en ninguna prueba de rechazo.
- [x] 1.5 Confirmar con `git --no-pager diff --stat` que solo cambió `AuthResourceTest`, y registrar el commit de línea base como cambio revisable por separado.

## 2. Reproducción del defecto H-AUTH-01

- [x] 2.1 Agregar la prueba de inyección en `username` (`' OR '1'='1` con contraseña no vacía) que espera `401` sin `token`; verificar localmente que **falla** con el código actual por responder `200` con `token`.
- [x] 2.2 Agregar la prueba de inyección en `password` (`username` `student`, `password` `' OR '1'='1`) que espera `401` sin `token`; verificar localmente que **falla** con el código actual por responder `200` con `token`.

## 3. Corrección

- [x] 3.1 En `LegacyDatabase.findByCredentials`, sustituir la concatenación por una sentencia preparada con `WHERE username = ? AND password = ?` y `setString` para ambos valores; conservar la firma, el mapeo a `UserRecord`, el cierre de recursos con `try-with-resources` y el `catch` que devuelve `null`. Verificar con `git --no-pager diff` que no queda concatenación de `username` ni `password` en el SQL y que no cambió ningún otro archivo de `src/main`.
- [x] 3.2 Ejecutar `mvn test` desde `auth/` y verificar que pasan las pruebas de línea base (grupo 1) y las dos de inyección (grupo 2) sin modificar las pruebas.

## 4. Validación final

- [x] 4.1 Ejecutar `mvn verify` desde `auth/` y verificar que termina sin fallos y que el informe de JaCoCo muestra cobertura de `findByCredentials` de 85 % o más; si no se alcanza, registrar el valor y detenerse para revisión en lugar de ampliar el alcance.
- [x] 4.2 Verificar contra `docs/ENDPOINTS.md` y los escenarios de `specs/auth-login/spec.md` que ninguna respuesta cambió para credenciales válidas, campos vacíos o credenciales no coincidentes, y que `AuthResource`, `pom.xml`, `api/` y `web/` no tienen cambios (`git --no-pager status --short`).
- [x] 4.3 Ejecutar `openspec validate "h-auth-01-parameterize-login-query" --strict` desde la raíz y verificar que el cambio sigue siendo válido.

## Workflow follow-up

- Revisión y aprobación humanas del cambio antes de integrar; no inventar la aprobación.
- Integración local según el cierre del Día 1 (sin push, PR ni remotos nuevos).
- Archivar el cambio OpenSpec solo después de la revisión y de la integración, y verificar el resultado archivado.
