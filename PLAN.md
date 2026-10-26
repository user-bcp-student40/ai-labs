# Plan de trabajo

## Alcance web

Se seleccionaron H-WEB-01 a H-WEB-06 cuando estaban `Pendiente` en `HALLAZGOS.md`. H-WEB-07 está marcado `No encontrado` y queda fuera del plan. Solo H-WEB-01 tuvo aprobación humana y se implementó; ahora figura `Resuelto`. H-WEB-02 a H-WEB-06 siguen sin autorización de implementación.

## Registro de revisión humana

| fecha | componente | hallazgo(s) autorizado(s) | revisor/a | decisión y condiciones |
|---|---|---|---|---|
| 2026-10-26 | web | H-WEB-01 | LT | Aprobado. Acepta usar `sessionStorage` y que la sesión termine al cerrar la pestaña. |

`docs/ENDPOINTS.md` no existe. Antes del cambio, la caracterización confirmó el comportamiento observado en `HALLAZGOS.md`: el login envía `POST http://localhost:8080/auth/login` con `username`, `password` y `client`; guarda token y usuario en `localStorage`, y navega al dashboard; el dashboard usa el token para solicitar tareas y cerrar sesión elimina token y usuario. Tras la aprobación específica de H-WEB-01, el flujo HTTP y las navegaciones se conservaron, pero token y usuario se trasladaron a `sessionStorage`; las preferencias permanecen en `localStorage`. Esto no establece un contrato acordado con los servicios.

Orden de trabajo propuesto: escribir y ejecutar caracterización antes de refactorizar (H-WEB-03); cambiar presentación de mensajes y almacenamiento (H-WEB-02, H-WEB-01); separar servicios y configuración (H-WEB-04); tipar el flujo (H-WEB-06); revisar dependencias con evidencia y decidir si se modifican (H-WEB-05). Las pruebas de cada etapa deben pasar antes de continuar. No se agregan dependencias en esta propuesta.

## H-WEB-01 — Token de sesión en `localStorage`

- **Hallazgo:** H-WEB-01, seleccionado cuando estaba `Pendiente` y ahora `Resuelto` en `HALLAZGOS.md`; implementación autorizada en el registro de revisión humana.
- **Problema:** el token persiste en `localStorage` y es accesible al JavaScript del origen. La lectura confirma el almacenamiento, pero no una vía de explotación concreta.
- **Cambio propuesto y ejecutado:** alternativa acotada: encapsular lectura, escritura y borrado de la sesión en un único servicio web y almacenar el token en `sessionStorage`. Esto reduce la persistencia entre sesiones de pestaña, pero no protege el token frente a JavaScript malicioso mientras la pestaña está abierta. Una cookie `HttpOnly` requeriría coordinación y cambios fuera de `web/`, por lo que no se implementó. LT confirmó que acepta perder la sesión al cerrar la pestaña; no se presenta `sessionStorage` como solución completa a XSS.
- **Archivos web previstos:** `web/src/app/login/login.component.ts`, `web/src/app/dashboard/dashboard.component.ts`; nuevo servicio de sesión bajo `web/src/app/` y su prueba.
- **Caracterización antes del cambio:** probar que, con respuesta de login que contiene token/usuario, se guardan token y usuario, se navega a `/dashboard`, el dashboard envía el token como Bearer y logout elimina ambos valores y navega a `/login`. Registrar el comportamiento actual de persistencia al recargar; la prueba de caracterización no implica conservar `localStorage` tras adoptar `sessionStorage`.
- **Verificación posterior:** las aserciones de la caracterización pasan con `sessionStorage`, token/usuario no se escriben en `localStorage`, el dashboard conserva la cabecera Bearer y logout limpia la sesión. La decisión humana acepta que la sesión termina al cerrar la pestaña. No se ejecutó una prueba real de ciclo de vida del navegador ni una integración con los servicios.

## H-WEB-02 — Mensajes dinámicos renderizados con `[innerHTML]`

- **Hallazgo:** H-WEB-02, `Pendiente` en `HALLAZGOS.md`.
- **Problema:** el template presenta como HTML un mensaje que concatena el usuario y texto procedente del error. El código leído no prueba ejecución de contenido; debe evitarse depender del contexto HTML para presentar texto dinámico.
- **Cambio propuesto:** mostrar mensajes mediante interpolación Angular como texto. Sustituir fragmentos HTML construidos en TypeScript por mensajes de texto; si se requiere conservar el salto entre encabezado y detalle, usar texto con salto de línea y estilo de presentación, no marcado dinámico. No cambiar el endpoint ni el flujo de respuestas.
- **Archivos web previstos:** `web/src/app/login/login.component.ts`, `web/src/app/login/login.component.html`, posiblemente `web/src/app/login/login.component.css`, y pruebas del componente.
- **Caracterización antes del cambio:** probar mensajes actuales de campos vacíos, respuesta sin token y error HTTP, incluyendo qué datos del mensaje se muestran. Conservar como baseline el significado del mensaje, no exigir que se ejecute HTML.
- **Verificación posterior:** entregar un usuario y un mensaje de error ficticios con texto similar a marcado y comprobar que el DOM lo presenta como texto, no como elementos interpretados; comprobar también mensajes de validación y error.

## H-WEB-03 — Falta de pruebas del flujo de login y dashboard

- **Hallazgo:** H-WEB-03, `Pendiente` en `HALLAZGOS.md`.
- **Problema:** la prueba encontrada cubre `formatTaskLabel`, pero no caracteriza login, almacenamiento de sesión, manejo de errores, consulta de tareas ni logout.
- **Cambio propuesto:** crear pruebas de caracterización para los flujos existentes antes de refactorizar H-WEB-01, H-WEB-02, H-WEB-04 y H-WEB-06. Usar Vitest y las dependencias instaladas; no añadir librerías sin justificar y aprobar. Si la configuración actual no permite probar Angular/componentes con mocks fiables, registrar el bloqueo y solicitar decisión antes de ampliar tooling.
- **Archivos web previstos:** nuevos `*.spec.ts` para login y dashboard bajo sus carpetas `web/src/app/login/` y `web/src/app/dashboard/`; cambios de configuración solo si se demuestra que son imprescindibles y se aprueban.
- **Caracterización antes de cambios funcionales:** cubrir campos vacíos sin petición HTTP; login válido con payload y timeout observados; respuesta sin token; rechazo HTTP; estado `busy`; persistencia y navegación; dashboard sin token; carga de tareas con cabecera Bearer; filtrado de archivadas/error; logout. Usar respuestas y credenciales ficticias.
- **Verificación posterior:** ejecutar `npm test` y `npm run build` desde `web/`; registrar resultados reales y asociarlos a H-WEB-03 y a los IDs cuyo comportamiento cubran.

## H-WEB-04 — HTTP, URLs, sesión y navegación acoplados a componentes

- **Hallazgo:** H-WEB-04, `Pendiente` en `HALLAZGOS.md`.
- **Problema:** los componentes hacen solicitudes Axios directamente y combinan integración, configuración, estado de sesión y navegación. Esto dificulta probar cada responsabilidad por separado.
- **Cambio propuesto:** extraer llamadas de autenticación y tareas a servicios con responsabilidad única; centralizar acceso a sesión conforme a H-WEB-01; mover URLs a configuración de ambiente de `web/`. Los componentes conservan validación/presentación y navegación necesaria. Mantener método, URL, payload, timeout, query, cabeceras y forma de respuesta observados mientras no exista contrato acordado distinto.
- **Archivos web previstos:** `web/src/app/login/login.component.ts`, `web/src/app/dashboard/dashboard.component.ts`; nuevos servicios y sus pruebas bajo `web/src/app/`; configuración de ambiente y cableado de providers/imports si el patrón de Angular del proyecto lo requiere.
- **Caracterización antes del cambio:** probar exactamente la petición de login (`POST`, URL, cuerpo y timeout), el almacenamiento/navegación de éxito y error; probar la petición de tareas (`GET`, query `owner`, cabecera Bearer), la ruta sin token y logout.
- **Verificación posterior:** comprobar mediante mocks que los componentes delegan a servicios y que las solicitudes y transiciones conservan el baseline. No añadir duplicación de URLs o claves de almacenamiento entre componentes.

## H-WEB-05 — Versiones candidatas de Axios y Lodash

- **Hallazgo:** H-WEB-05, `Pendiente` en `HALLAZGOS.md`.
- **Problema:** `web/package.json` declara las versiones indicadas por el reto; su presencia está comprobada, pero este discovery no confirmó advisories ni un CVE.
- **Cambio propuesto:** consultar y documentar advisories para las dependencias efectivamente instaladas y sus rutas de uso. Coordinar cualquier actualización/eliminación con quien mantenga dependencias externas; no cambiar versiones ni lockfile hasta tener evidencia de impacto, una decisión aprobada y compatibilidad verificada. Preferir APIs nativas si bastan, evitando introducir dependencias nuevas.
- **Archivos web previstos si se aprueba una remediación:** `web/package.json`, `web/package-lock.json`, y solo los archivos web que usen la dependencia si se decide retirarla. No tocar lockfile en la fase de análisis.
- **Caracterización antes de cambios:** establecer baseline ejecutando `npm test` y `npm run build` desde `web/`; registrar el resultado de `npm run audit:workshop` por separado si se ejecuta y distinguir advisories de CVEs confirmados. No afirmar que el audit estático resuelve el impacto en runtime.
- **Verificación posterior:** repetir pruebas/build y auditoría tras una actualización aprobada; comparar versiones resueltas y revisar que los usos del código sigan funcionando. Hasta entonces, dejar el hallazgo Pendiente.

## H-WEB-06 — Tipos `any` y validación anidada

- **Hallazgo:** H-WEB-06, `Pendiente` en `HALLAZGOS.md`.
- **Problema:** `any` en estado y respuestas elimina comprobaciones estáticas; las validaciones anidadas dificultan seguir los retornos de error.
- **Cambio propuesto:** definir tipos para credenciales, respuesta de login/usuario, tareas y estado; sustituir `any` por tipos concretos y tratar errores como `unknown` con guardas. Simplificar validaciones con retornos anticipados cuando preserve el comportamiento. Usar constantes existentes o con nombre para valores de configuración repetidos; evitar duplicación con los servicios de H-WEB-04.
- **Archivos web previstos:** `web/src/app/login/login.component.ts`, `web/src/app/dashboard/dashboard.component.ts`, utilidades/modelos tipados nuevos bajo `web/src/app/` solo si son necesarios, y pruebas correspondientes.
- **Caracterización antes del cambio:** cubrir validaciones de usuario/contraseña vacíos, login exitoso y respuesta sin token, error de red/API y restauración de `busy`; en dashboard, ausencia de token y respuestas de tareas con estados archivados/no archivados. Asegurar que las pruebas afirman el resultado observable y no los tipos internos.
- **Verificación posterior:** repetir la suite y build para detectar incompatibilidades de tipos; comprobar que los mismos caminos HTTP, mensajes, almacenamiento y navegación permanecen.

## Pendientes y límites

- No hay contrato acordado en `docs/ENDPOINTS.md`; solo se verificó el flujo mediante mocks locales, sin integrar con los servicios HTTP.
- No se ejecutó prueba en navegador para comprobar el cierre de la sesión al cerrar la pestaña; el comportamiento depende de la semántica de `sessionStorage`.
- No se consultaron advisories ni se actualizaron dependencias. H-WEB-02 a H-WEB-06 siguen sin autorización y sin cambios; H-WEB-07 continúa `No encontrado`.
- La cobertura global reportada por Vitest es menor a 85% porque incluye archivos no modificados. Los archivos de implementación afectados superan 85%; ver los porcentajes en el registro.
- Las líneas de evidencia y estados vigentes se mantienen en `HALLAZGOS.md`; actualizar cada estado solo con evidencia y revisión correspondientes.

## Ejecuciones registradas

| fecha | componente | ID(s) | etapa | comando | resultado |
|---|---|---|---|---|---|
| 2026-10-26 | web | H-WEB-01 | Caracterización previa | `npm test -- --reporter=verbose` (cwd `web/`) | Falló al cargar componentes: Vitest no había cargado el compilador JIT de Angular. |
| 2026-10-26 | web | H-WEB-01 | Caracterización previa | `npm test -- --reporter=verbose` (cwd `web/`) | Falló: el mock de Axios no exponía `AxiosHeaders`. |
| 2026-10-26 | web | H-WEB-01 | Caracterización previa | `npm test -- --reporter=verbose` (cwd `web/`) | Falló con el mismo error de `AxiosHeaders`; se reemplazó su uso en la prueba por cabeceras estructurales. |
| 2026-10-26 | web | H-WEB-01 | Caracterización previa | `npm test -- --reporter=verbose` (cwd `web/`) | Pasó: 2 archivos y 2 pruebas; la caracterización confirma login, almacenamiento actual, consulta de tareas con token y logout antes del cambio. |
| 2026-10-26 | web | H-WEB-01 | Corrección y primera medición | `npm run test:coverage` (cwd `web/`) | Pasó 2 archivos/2 pruebas; cobertura: login 84,74%, dashboard 84,72%, servicio de sesión 100%, global 73,26%. Los dos componentes quedaron por debajo de 85%; se añadieron dos casos de token vacío/ausente. |
| 2026-10-26 | web | H-WEB-01 | Build de corrección | `npm run build` (cwd `web/`) | Pasó. Angular informó advertencias CommonJS existentes para Axios y Lodash; no se ocultaron ni se modificaron dependencias. |
| 2026-10-26 | web | H-WEB-01 | Regresión y cobertura final | `npm run test:coverage` (cwd `web/`) | Pasó 2 archivos/4 pruebas. Cobertura: login 88,13%, dashboard 88,88%, servicio de sesión 100%; global 75,93%. Los tres archivos de implementación afectados superan 85%; la suite completa no alcanza 85% global. |
