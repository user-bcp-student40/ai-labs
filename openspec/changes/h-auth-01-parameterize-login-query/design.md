# Design

## Context

Motivación y alcance en `proposal.md` (Issue #22, H-AUTH-01); requisitos en `specs/auth-login/spec.md`. Componente afectado: solo `auth/` (Quarkus 3.27, Java 21, SQLite vía `sqlite-jdbc`).

Estado actual relevante, verificado en código:

- `AuthResource.login` (`POST /auth/login`) valida que `username` y `password` no sean nulos ni estén en blanco (`400`), llama a `LegacyDatabase.findByCredentials(username, password)` y, si devuelve `null`, responde `401`; si no, arma el token y la respuesta `200`. Los valores se pasan **sin recortar** a la base.
- `LegacyDatabase.findByCredentials` concatena ambos valores en un `Statement` (`SELECT id, username, display_name, role FROM legacy_users WHERE username='…' AND password='…'`), abre una conexión por llamada con `DriverManager` y captura cualquier `Exception`, la imprime y devuelve `null`. Hoy un error de SQL termina en `401`, no en `500`.
- El resto de SQL de la clase (`initialize`) usa literales constantes, sin datos de entrada.
- `AuthResourceTest` solo cubre el login válido. La base es un archivo SQLite (`AUTH_DB_URL`, por defecto `jdbc:sqlite:./data/workshop.db`) sembrado en `@PostConstruct` con `student` y `trainer`; los tests la comparten.
- `pom.xml` ya incluye `jacoco-maven-plugin` (el informe se genera en la fase `verify`).

Efecto observable del defecto: con `username=student` y `password=' OR '1'='1` la condición pasa a `… AND password='' OR '1'='1'`, que es verdadera para toda fila, y el login responde `200` con token.

## Goals / Non-Goals

**Goals:**
- Que `findByCredentials` envíe `username` y `password` a la base como parámetros enlazados, sin concatenarlos en el SQL.
- Que el cambio sea acotado a ese método y sea reversible con un solo `git revert`.
- Que las pruebas fijen primero el comportamiento actual y después demuestren la corrección del defecto.

**Non-Goals:**
- Introducir hashing de contraseñas, migrar el esquema o los datos de `legacy_users`.
- Cambiar la firma de `findByCredentials`, el tipo `UserRecord`, el flujo de `AuthResource.login` o la estrategia de conexión (`DriverManager`, una conexión por llamada).
- Cambiar el manejo de errores de la base (seguir devolviendo `null` → `401`) ni el logging con `printStackTrace`.
- Añadir dependencias, pool de conexiones, ORM o validación de formato de entrada.
- Corregir el mensaje de 401 que refleja el usuario, el campo `debug` ni el detalle de excepciones en `500` (fuera de alcance en la propuesta).

## Contratos protegidos

Baseline en `docs/ENDPOINTS.md` y en los requisitos de `specs/auth-login/spec.md`. El Issue no cambia ninguno de ellos.

| Contrato | Qué debe seguir igual |
|---|---|
| `POST /auth/login` (ruta, método, cuerpo `username`/`password`/`client`) | Idéntico; propiedades JSON desconocidas siguen ignoradas (`fail-on-unknown-properties=false`). |
| Respuesta `200` | `token`, `expiresIn`, `user.username`, `user.displayName` (escapado), `user.role` y `debug` se conservan; el cliente Angular exige `token` truthy y guarda `user`. |
| `400` | Mismas reglas de campos ausentes o en blanco, evaluadas antes de tocar la base. |
| `401` | Credenciales que no coinciden, incluidos los errores internos de la base, siguen produciendo `401` sin `token`. |
| Firma de `LegacyDatabase.findByCredentials(String, String)` → `UserRecord` o `null` | Sin cambios; `AuthResource` no se modifica. |
| Semántica de comparación | Coincidencia exacta de `username` y `password`, sensible a mayúsculas, sin recorte de espacios, igual que hoy. |

## Componentes afectados

- Modificado: `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java`, solo el cuerpo de `findByCredentials`.
- Modificado: `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java`, nuevas pruebas.
- Sin cambios: `AuthResource`, `LegacyTokenUtil`, `LoginRequest`, `UserRecord`, `application.properties`, `pom.xml`, `api/`, `web/`.

## Decisions

### D1. Consulta con `PreparedStatement` y marcadores `?`

`findByCredentials` pasa a usar una sentencia preparada con `WHERE username = ? AND password = ?`, enlazando los valores con `setString`, y mantiene los mismos `try-with-resources` (conexión, sentencia, `ResultSet`), el mismo mapeo a `UserRecord` y el mismo `catch` que devuelve `null`.

Por qué: es el mecanismo estándar de JDBC, lo pide el criterio del Issue, no agrega dependencias y conserva la semántica de comparación exacta (SQLite compara texto con colación binaria, igual que con los literales actuales). Los valores dejan de interpretarse como sintaxis SQL.

Alternativas consideradas:
- *Escapar comillas manualmente:* frágil y dependiente del motor; no elimina la clase de defecto. Descartada.
- *Lista negra o validación de caracteres en `AuthResource`:* rechazaría contraseñas legítimas y altera el contrato `400`/`401`. Descartada.
- *Consultar solo por `username` y comparar la contraseña en Java:* también es seguro, pero cambia dónde ocurre la comparación y se acerca al tema de contraseñas, que está fuera de alcance. Descartada.
- *Panache, JPA o `quarkus-agroal`:* dependencias y refactor de persistencia desproporcionados para un defecto de una línea. Descartada.

### D2. Mantener el manejo de errores existente

Si la base falla, el método sigue devolviendo `null` y el recurso responde `401` (comportamiento que falla cerrado: nunca emite token). Cambiarlo a `500` sería un cambio de contrato no pedido por el Issue.

Alternativa: propagar la excepción. Descartada por alterar el contrato y mezclar un cambio de comportamiento con una corrección de seguridad.

### D3. Las pruebas de integración van por HTTP en `AuthResourceTest`

Se usa el mismo estilo existente (`@QuarkusTest` + RestAssured) contra `/auth/login`, porque los requisitos están expresados como comportamiento HTTP. Las pruebas no escriben en la base y solo usan las credenciales de laboratorio ya sembradas, sin secretos reales. Las pruebas de rechazo verifican el código de estado y la ausencia de `token`; no fijan el texto del mensaje de 401, para no congelar el comportamiento que la propuesta deja fuera de alcance.

Alternativa: prueba unitaria directa de `LegacyDatabase`. Requeriría controlar `AUTH_DB_URL`, que se lee en un campo estático; no justifica cambiar la clase solo para eso.

## Pruebas de caracterización necesarias antes de modificar

Se escriben y se ejecutan **contra el código actual**, antes de tocar `LegacyDatabase`:

| Prueba | Escenario de la spec | Resultado esperado con el código actual |
|---|---|---|
| Login válido (ya existe), reforzado con `expiresIn`, `user.displayName` y `user.role` | Login con credenciales válidas | Pasa |
| Contraseña incorrecta para `student` | Contraseña incorrecta | Pasa (`401`, sin `token`) |
| Usuario inexistente | Usuario inexistente | Pasa |
| `username` en blanco; `password` ausente | Validación de campos obligatorios | Pasa (`400`, sin `token`) |
| `username` con comilla simple que no existe | Comillas en credencial no válida | Pasa (`401`, hoy por el error de SQL capturado) |
| Inyección en `username` (`' OR '1'='1`) | Intento de inyección en el usuario | **Falla** (devuelve `200` con `token`): evidencia del defecto |
| Inyección en `password` con `username=student` | Intento de inyección en la contraseña | **Falla** (devuelve `200` con `token`): evidencia del defecto |

Las dos pruebas rojas se ejecutan localmente para confirmar que reproducen H-AUTH-01 antes de corregir; luego deben pasar con D1 sin tocar el resto.

## Estrategia incremental

1. **Línea base:** añadir las pruebas de caracterización que pasan hoy y ejecutar `mvn test` desde `auth/`. Un cambio revisable por sí solo.
2. **Reproducir:** añadir las dos pruebas de inyección y confirmar localmente que fallan con el código actual.
3. **Corregir:** aplicar D1 en `findByCredentials`, sin otros cambios. Con esto las pruebas de inyección pasan junto con las de línea base.
4. **Verificar:** `mvn test` desde `auth/` y `mvn verify` para el informe de JaCoCo. La cobertura del código modificado debe ser de 85 % o más. Revisar que el workflow de CodeQL siga activo, sin suprimir alertas; se espera, sin haberlo verificado, que la alerta de inyección SQL de esa consulta desaparezca.

Los pasos 2 y 3 pueden ir en el mismo commit para no dejar un commit con pruebas rojas en la rama; el paso 1 va aparte. No hay push durante el Día 1.

## Risks / Trade-offs

- [Una prueba de inyección pasa por la razón equivocada: hoy un `'` provoca error SQL y devuelve `401`] → Las pruebas de inyección usan un payload que hoy devuelve `200`; verificarlas rojas en el paso 2 demuestra que detectan el defecto.
- [Diferencia sutil de comparación entre literal y parámetro] → SQLite aplica la misma colación binaria en ambos casos; la prueba de login válido y la de contraseña incorrecta lo cubren, incluida una variante con distinta capitalización.
- [El `catch` que devuelve `null` oculta errores de la base] → Riesgo preexistente, fuera de alcance; mitigado porque falla cerrado y queda registrado como deuda separada.
- [Cobertura: las líneas del `catch` no se ejercitan con pruebas HTTP] → Representan una fracción pequeña del método; se mide con JaCoCo en `mvn verify` y, si la meta de 85 % no se alcanza, se evalúa entonces una prueba específica sin ampliar el alcance.
- [Pruebas que comparten el archivo `./data/workshop.db`] → Las pruebas son de solo lectura sobre usuarios sembrados; no introducen estado nuevo.
- [Esta corrección no elimina las contraseñas en texto plano] → Documentado como fuera de alcance; la corrección de H-AUTH-01 no debe presentarse como cierre de ese riesgo.

## Rollback

El cambio es de código puro: no hay migración de datos, esquema ni configuración. Para revertir basta `git revert` del commit de la corrección (y, si se desea, de las pruebas). Revertir restaura la vulnerabilidad, por lo que solo se justifica si la corrección rompe el login válido; las pruebas de línea base detectarían ese caso antes de integrar.
