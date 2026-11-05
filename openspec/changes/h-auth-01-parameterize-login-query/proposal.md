# Proposal

## Why

Issue [#22](https://github.com/user-bcp-student40/ai-labs/issues/22) (hallazgo origen **H-AUTH-01**, componente `auth`, vulnerabilidad de severidad alta) reporta que la consulta de credenciales del login se construye concatenando `username` y `password` (`auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:32`). Un valor como `' OR '1'='1` altera la consulta y permite obtener un token sin conocer la contraseña, lo que rompe la garantía básica de `POST /auth/login`: solo credenciales válidas producen una sesión.

## What Changes

- Los valores `username` y `password` recibidos en `POST /auth/login` se tratan siempre como datos de la consulta de credenciales, nunca como parte de su sintaxis; la consulta usa parámetros (criterio del Issue: `PreparedStatement` con parámetros, sin concatenar valores).
- Un intento de inyección SQL en `username` o `password` responde `401` y no devuelve `token`.
- Se agrega una prueba de caracterización del intento de inyección a `AuthResourceTest`, y `mvn test` debe pasar desde `auth/`.
- No hay cambios **BREAKING**: ningún campo, código de estado ni formato de respuesta cambia para credenciales válidas ni para entradas ya rechazadas.

## Capabilities

### New Capabilities
- `auth-login`: autenticación por credenciales en `POST /auth/login`. El repositorio no tiene specs previas (`openspec list --specs` está vacío), así que esta spec fija como baseline el comportamiento que se debe conservar y agrega el requisito de resistencia a inyección SQL.

### Modified Capabilities
<!-- Ninguna: no existen capacidades previas en openspec/specs/. -->

## Alcance

**Dentro de alcance**
- Consulta de credenciales de `LegacyDatabase.findByCredentials` en `auth/`.
- Comportamiento observable de `POST /auth/login` ante credenciales válidas, inválidas y con intento de inyección.
- Prueba del intento de inyección en `AuthResourceTest`.

**Fuera de alcance**
- Almacenamiento de contraseñas en texto plano en `legacy_users` y su siembra inicial.
- Generación, firma y expiración del token (`LegacyTokenUtil`, `expiresIn`).
- Mensaje de 401 que incluye el usuario recibido, campo `debug` de la respuesta y detalle de excepción en respuestas 500.
- Refactorización de `AuthResource.login` en capas, y cualquier cambio en `api/` o `web/`.
- Limitación de intentos, auditoría o bloqueo de cuentas.

## Comportamiento que debe preservarse

Baseline: `docs/ENDPOINTS.md` (contrato documentado el Día 1: `POST http://localhost:8080/auth/login`, cuerpo JSON con `username`, `password` y `client`; el cliente exige un `token` truthy y guarda `user`) y el comportamiento observado en `AuthResource.login` y `AuthResourceTest`. `docs/ENDPOINTS.md` deja pendiente confirmar los códigos exactos del servidor; las specs usan los observados en el código y los fijados por el Issue (200 y 401). El Issue no cambia este contrato.

- Credenciales válidas (`student` / `Workshop123!`) → `200` con `token` y `user.username`; la respuesta mantiene además `expiresIn`, `user.displayName` y `user.role`.
- `username` o `password` ausentes o en blanco → `400` sin `token`.
- Credenciales válidas pero no coincidentes → `401` sin `token`.
- Sin secretos reales: se usan solo las credenciales de laboratorio ya documentadas.

## Impact

- Código: `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java` (consulta de credenciales) y `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java` (nueva prueba).
- API: sin cambios de contrato para `POST /auth/login`; `web/` y `api/` no se tocan.
- Dependencias: ninguna nueva.
- Validación: `mvn test` desde `auth/`; cobertura del código modificado de 85 % o superior.
