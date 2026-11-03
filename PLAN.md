# Plan de trabajo

## Alcance web

Se seleccionaron H-WEB-01 a H-WEB-06 cuando estaban `Pendiente` en `HALLAZGOS.md`. H-WEB-07 está marcado `No encontrado` y queda fuera del plan. Solo H-WEB-01 tuvo aprobación humana y se implementó; ahora figura `Resuelto`. H-WEB-02 a H-WEB-06 siguen sin autorización de implementación.

## Registro de revisión humana

| fecha | componente | hallazgo(s) autorizado(s) | revisor/a | decisión y condiciones |
|---|---|---|---|---|
| 2026-10-26 | web | H-WEB-01 | LT | Aprobado. Acepta usar `sessionStorage` y que la sesión termine al cerrar la pestaña. |
| 2026-11-02 | api | H-API-01 a H-API-12 | CARLOS VALDIVIA | Aprobado. Sin condiciones adicionales. |

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

## Alcance api

Se incluyen H-API-01 a H-API-12 porque sus filas en `HALLAZGOS.md` están
marcadas `Aprobado`. H-API-07, H-API-08, H-API-11 y H-API-12 son deuda adicional
de discovery, no hallazgos sembrados por `RETO.md`. La selección y el motivo
técnico de inclusión son:

| ID(s) | motivo técnico de inclusión |
|---|---|
| H-API-01 a H-API-04 | Hallazgos de severidad alta relacionados con SQL, token, autorización y carga de archivos. |
| H-API-05 a H-API-06 | Dependencias con CVE/versiones afectadas que requieren verificación y corrección coordinada. |
| H-API-07 a H-API-08 | Errores que exponen detalles internos y CORS demasiado permisivo, identificados en discovery. |
| H-API-09 a H-API-10 | Deuda de arquitectura y calidad que afecta separación de responsabilidades, tipado y mantenibilidad. |
| H-API-11 | Candidato de concurrencia aprobado para verificación con carga antes de decidir una solución. |
| H-API-12 | Cobertura de pruebas insuficiente para caracterizar y demostrar las correcciones anteriores. |

El estado `Aprobado` se verificó en las doce filas de `HALLAZGOS.md`. El
registro de revisión humana de este plan consigna para `api` la fecha
2026-11-02, la persona revisora CARLOS VALDIVIA y la autorización de
H-API-01 a H-API-12 sin condiciones adicionales. La selección y los motivos
técnicos de inclusión descritos aquí no se presentan como motivos expresados
por la persona revisora.

`docs/ENDPOINTS.md` describe el contrato observado por `web`, pero no documenta
ni confirma el contrato de `api`. Para esta propuesta se protege el
comportamiento observado en `api/app/main.py`: métodos, rutas, estados de éxito,
campos y formas de respuesta; la autenticación usa actualmente un token Base64
casero. Un acuerdo de contrato con los responsables del emisor de tokens, los
roles, CORS y las reglas de archivos sigue pendiente. Los cambios de autorización
y token podrían alterar el comportamiento existente y no deben integrarse hasta
resolver esas dependencias.

### Estrategia incremental propuesta para los hallazgos aprobados

1. Añadir pruebas de caracterización del HTTP actual y de los límites conocidos,
   con datos aislados y sin modificar aún el código de ejecución. Registrar el
   baseline real antes de cada cambio.
2. Remediar consultas y autorización (H-API-01, H-API-03); resolver el contrato
   del token antes de reemplazarlo (H-API-02); establecer y probar la política de
   archivos antes de endurecer cargas (H-API-04).
3. Coordinar y verificar las actualizaciones de dependencias (H-API-05,
   H-API-06); corregir exposición de errores y CORS (H-API-07, H-API-08).
4. Separar capas gradualmente (H-API-09), consolidando modelos y calidad de
   código (H-API-10) y usando las pruebas del conjunto como protección. Resolver
   el acceso concurrente a SQLite con evidencia (H-API-11) y ampliar cobertura
   transversalmente (H-API-12).

En cada etapa, conservar los contratos HTTP observados que no dependan del
comportamiento vulnerable, revisar el diff y ejecutar pruebas desde `api/`.
No añadir dependencias de runtime sin documentar necesidad, opciones evaluadas
y aprobación; no introducir secretos reales. La meta de cobertura para el
código modificado es 85% o superior, sin reducir gates ni silenciar scanners.

## H-API-01 — Concatenación de SQL en filtros e inserciones de tareas

- **Hallazgo:** H-API-01, ahora `Resuelto` en `HALLAZGOS.md`.
- **Problema:** filtros de tareas/resumen e inserciones incorporan valores
  recibidos en sentencias SQL como texto; una comilla puede alterar la consulta,
  romper una operación o afectar qué filas se consultan.
- **Cambio propuesto:** mover acceso SQL a repositorio según H-API-09 y usar
  placeholders SQLite para cada valor (`owner`, campos de tarea e ID); mantener
  la selección de columnas constante, no interpolada. No cambiar orden,
  columnas, estados HTTP ni forma de respuesta.
- **Archivos api previstos:** `api/app/main.py` durante el cambio inicial o el
  router/servicio/repositorio que se acuerde en H-API-09; `api/tests/test_api.py`
  y pruebas del repositorio si se separa.
- **Caracterización antes de tocar implementación:** comprobar listado y resumen
  para usuario normal, inserción y recuperación de tarea, valores vacíos y
  valores de texto con caracteres de puntuación tratados como datos; registrar
  el comportamiento actual sin usar payloads de explotación. Después, verificar
  que cada valor se almacena/filtra literalmente, no cambia la consulta y se
  conserva la respuesta observada.
- **Ejecución real:** `python -m pytest --cov=app --cov-report=term-missing`
  (cwd `api/`), baseline: 4 pruebas pasaron, cobertura total 91%. Se añadió
  primero una caracterización con apóstrofos; antes del cambio falló con
  `sqlite3.OperationalError: near "s": syntax error` al insertar. Después de
  parametrizar filtros, inserción y recuperación por ID, la suite pasó: 5
  pruebas, cobertura total 91%. El resultado detallado también consta en
  «Ejecuciones api» al final de este plan.

## H-API-02 — Token Base64 sin firma y con secreto fijo

- **Hallazgo:** H-API-02, `Aprobado` en `HALLAZGOS.md`.
- **Problema:** Base64 no proporciona integridad y el secreto está fijado en el
  código; la aceptación de identidad depende de contenido que no está firmado.
- **Cambio propuesto:** reemplazarlo por validación estricta de JWT firmado,
  incluida firma, algoritmo permitido, emisor, audiencia y expiración, como
  indica `docs/GOOD_PRACTICES.md`. Obtener emisor, audiencia, algoritmo y
  material de verificación del responsable del emisor de tokens; configurar
  secretos solo por entorno si el acuerdo requiere secreto compartido. Evaluar
  primero una biblioteca ya disponible; si hace falta una dependencia, justificar
  cuál y sus riesgos antes de proponer añadirla. No aceptar silenciosamente el
  formato antiguo como fallback.
- **Archivos api previstos:** módulo de seguridad/token en `api/app/` (o
  `api/app/main.py` si el cambio inicial permanece acotado), configuración de
  `api/` solo si se acuerda, `api/tests/test_api.py` y pruebas nuevas del módulo.
- **Caracterización antes de tocar implementación:** cubrir token heredado de
  laboratorio vigente, expirado, malformado y ausente, y respuesta 401
  observada; guardar ese baseline sin ampliar validez. Antes del cambio JWT,
  añadir pruebas para firma válida, firma inválida, expiración, emisor/audiencia
  erróneos y cabecera/esquema incorrectos. Las pruebas JWT requieren primero
  conocer el contrato del emisor; usar exclusivamente claves ficticias aisladas.

## H-API-03 — Autorización por `owner` del cliente y rol sin uso

- **Hallazgo:** H-API-03, `Aprobado` en `HALLAZGOS.md`.
- **Problema:** el cliente puede seleccionar owner en lectura y escritura; el
  rol del token no se utiliza para autorizar. La identidad autenticada no es la
  fuente única del ámbito de datos.
- **Cambio propuesto:** derivar el owner efectivo de la identidad verificada.
  Mantener el parámetro `owner` para compatibilidad sintáctica si el contrato
  lo exige, pero no permitir que amplíe el acceso. Definir con responsables si
  un owner distinto se rechaza (403) o se ignora, y si existe un rol
  administrativo con acceso cruzado; no inferir roles ni privilegios. En
  creación, establecer el owner desde identidad, no desde el cuerpo.
- **Archivos api previstos:** router de tareas/resumen y servicio de
  autorización bajo `api/app/` (o `api/app/main.py` en primer paso),
  `api/tests/test_api.py` y posibles pruebas de servicio.
- **Caracterización antes de tocar implementación:** probar que el owner
  omitido usa el usuario autenticado; caracterizar la respuesta actual cuando
  query/cuerpo señalan otro owner y la salida observada de GET/POST/summary.
  Añadir pruebas de aceptación posteriores para dos identidades aisladas y para
  el rol administrativo únicamente cuando el contrato de roles se acuerde.
  Verificar que la UI que envía `owner` con el nombre propio conserva sus
  respuestas y que la petición con owner distinto no revela ni crea datos ajenos.

## H-API-04 — Nombre de archivo sin normalizar ni límites de carga

- **Hallazgo:** H-API-04, `Aprobado` en `HALLAZGOS.md`.
- **Problema:** el nombre provisto por cliente se usa como ruta, el archivo se
  lee completo y no se restringen tamaño ni extensión; puede ocurrir escritura
  fuera del directorio, sobrescritura, consumo excesivo de memoria o persistencia
  de tipos no admitidos.
- **Cambio propuesto:** acordar extensión permitida y tamaño máximo; definir
  constantes nombradas, validar antes de persistir, normalizar el nombre y
  garantizar que el destino permanezca dentro de la carpeta de carga. Escribir
  en streaming acotado al tamaño máximo y usar nombre seguro/no colisionante.
  Mantener `POST /api/requirements`, el campo `file`, estado 201 y campos de
  respuesta; decidir con responsables si `fileName` refleja nombre original o
  normalizado y si `storedAt` puede seguir revelándose.
- **Archivos api previstos:** ruta/servicio de carga bajo `api/app/` (o
  `api/app/main.py` para el cambio inicial), `api/tests/test_api.py`; archivo de
  configuración en `api/` solo si se aprueban valores configurables.
- **Caracterización antes de tocar implementación:** subir un archivo pequeño
  permitido con nombre simple ficticio y comprobar estado, claves de respuesta,
  tamaño y bytes guardados; registrar tratamiento de nombre repetido. Una vez
  acordada la política, probar extensión no permitida, nombre inválido y
  contenido por encima del límite, comprobando rechazo sin escritura fuera del
  directorio ni lectura ilimitada. No usar rutas o payloads de explotación.

## H-API-05 — `python-multipart 0.0.21` y CVE-2026-24486

- **Hallazgo:** H-API-05, ahora `Resuelto` en `HALLAZGOS.md`.
- **Problema:** OSV indica que versiones anteriores a 0.0.22 están afectadas
  por CVE-2026-24486 en configuraciones no predeterminadas de guardado de
  nombres; el código no configura esas opciones, pero fija la versión afectada.
- **Cambio propuesto:** confirmar paquete resuelto y advisory en el entorno
  objetivo y actualizar el pin a 0.0.22 o versión corregida compatible. Coordinar
  con quien mantiene dependencias externas; mantener un pin reproducible y no
  desactivar Dependency Review ni scanners.
- **Archivos api previstos:** `api/requirements.txt` y, si las pruebas demuestran
  necesidad, pruebas de carga en `api/tests/test_api.py`; no tocar otros
  componentes ni lockfiles inexistentes.
- **Caracterización antes de tocar dependencias:** registrar pruebas actuales de
  `POST /api/requirements` para multipart válido, archivo ausente y respuesta
  observada. Obtener baseline de instalación/auditoría (por ejemplo
  `pip-audit` si está disponible) y registrar resultado real antes de cambiar
  versión; después repetir tests y auditoría con el pin propuesto.
- **Ejecución real:** antes del cambio, las pruebas focalizadas de carga válida,
  archivo ausente y backend-health pasaron (3 pruebas) con los pins originales
  en `api/.venv`. Después de actualizar e instalar los pins, la suite pasó: 9
  pruebas y 97% de cobertura total. `pip-audit` no estaba instalado; no se
  afirmó ni ejecutó una auditoría automatizada. Véase «Ejecuciones api».

## H-API-06 — `urllib3 2.5.0` y CVE-2025-66418/CVE-2025-66471

- **Hallazgo:** H-API-06, ahora `Resuelto` en `HALLAZGOS.md`.
- **Problema:** OSV informa que ambas vulnerabilidades de consumo de recursos
  afectan versiones anteriores a 2.6.0; la integración `backend-health` usa
  `urllib3` para consultar la URL configurada.
- **Cambio propuesto:** confirmar paquete resuelto, advisory y compatibilidad;
  proponer versión corregida (2.6.0 o posterior compatible) en coordinación
  con mantenimiento de dependencias. Conservar timeout y esquema de respuesta
  observados; no silenciar alertas.
- **Archivos api previstos:** `api/requirements.txt`, pruebas en
  `api/tests/test_api.py`; si el mock requerido se extrae, módulo de cliente
  backend bajo `api/app/`.
- **Caracterización antes de tocar dependencias:** probar respuesta exitosa con
  status/body ficticios y error de conexión con la respuesta actual
  `status: 0`; registrar timeout de 3 segundos como configuración observada.
  Ejecutar auditoría de dependencias antes y después y las pruebas focalizadas
  con la versión propuesta.
- **Ejecución real:** la prueba de éxito de backend-health pasó antes del cambio
  con `urllib3 2.5.0` y luego quedó cubierta por la suite completa con
  `urllib3 2.6.0`; timeout, status y body esperados se conservaron. Se verificó
  la versión instalada con `pip show`. La auditoría `pip-audit` no se ejecutó
  porque no está instalada; queda pendiente.

## H-API-07 — Errores exponen detalles internos

- **Hallazgo:** H-API-07, ahora `Resuelto` en `HALLAZGOS.md` (deuda de discovery).
- **Problema:** la respuesta 401 y el fallback de `backend-health` incluyen
  texto crudo de excepciones, potencialmente revelando detalles de formato o
  red interna.
- **Cambio propuesto:** devolver mensajes genéricos, conservar el estado HTTP y
  las claves/formas JSON observadas (`detail` o `body`), y registrar detalles
  solo mediante logging controlado del servidor. Manejar excepciones específicas
  cuando sea posible; no ocultar fallos con respuestas que parezcan éxito.
- **Archivos api previstos:** seguridad y cliente de salud bajo `api/app/` (o
  `api/app/main.py` al inicio), `api/tests/test_api.py`.
- **Caracterización antes de tocar implementación:** probar token inválido y
  backend no disponible; registrar 401, estructura del detalle y respuesta
  `status: 0`. Después comprobar que el texto de cliente es genérico y estable,
  sin información de excepción, mientras el fallo queda observable en el log
  controlado.
- **Ejecución real:** primero las dos pruebas nuevas fallaron con el código
  anterior: el 401 incluía `Incorrect padding` y `backend-health` exponía el
  texto de la excepción simulada. Tras cambiar a mensajes genéricos, logging
  controlado y manejo de excepciones específicas, la suite pasó: 7 pruebas y
  96% de cobertura total (`python -m pytest --cov=app --cov-report=term-missing`,
  cwd `api/`). Véase «Ejecuciones api».

## H-API-08 — CORS con origen comodín y credenciales

- **Hallazgo:** H-API-08, `Aprobado` en `HALLAZGOS.md` (deuda de discovery).
- **Problema:** la configuración admite cualquier origen, método y cabecera con
  credenciales; amplía orígenes navegables y no expresa los sitios realmente
  permitidos.
- **Cambio propuesto:** restringir `allow_origins` a una lista explícita
  configurable y justificada por el despliegue; definir si se requieren
  credenciales de navegador, conservar la cabecera `Authorization` para el
  cliente observado y no abrir métodos/cabeceras innecesarios. El origen de
  producción y entornos adicionales requieren coordinación externa.
- **Archivos api previstos:** configuración de middleware en `api/app/main.py`
  o módulo de configuración bajo `api/app/`, más `api/tests/test_api.py`.
- **Caracterización antes de tocar implementación:** registrar preflight y
  respuesta actual para un origen de laboratorio, método y cabecera
  `Authorization`; comprobar qué campos CORS produce la configuración actual.
  Después probar origen local acordado permitido, origen no configurado
  rechazado/no autorizado y preflight de los métodos usados. No asumir que una
  configuración local define la lista de producción.

## H-API-09 — Rutas, DB, reglas y serialización en un archivo

- **Hallazgo:** H-API-09, `Aprobado` en `HALLAZGOS.md`.
- **Problema:** `api/app/main.py` combina inicialización, SQL, reglas,
  serialización y HTTP; además, importar el módulo crea la app y recursos por
  defecto. Esto acopla pruebas y dificulta aislar cambios.
- **Cambio propuesto:** separación incremental y reversible en routers,
  servicios y repositorios con responsabilidades únicas; mantener
  `create_app(db_path, upload_dir)` como punto de configuración de pruebas.
  Centralizar el mapeo de tarea y consultas compartidas sin duplicación.
  Posponer o preservar la creación de `app` de nivel módulo si la forma de
  arranque de Uvicorn depende de ella; no mover archivos fuera de `api/`.
- **Archivos api previstos:** reorganización de `api/app/main.py` y módulos
  nuevos solo bajo `api/app/`; `api/tests/test_api.py` y pruebas unitarias
  nuevas asociadas.
- **Caracterización antes de tocar implementación:** cubrir los cinco endpoints
  protegidos, inicialización de base aislada, semilla, autenticación, métodos,
  códigos, request/response y cierre de app; capturar contrato HTTP observado
  antes de mover cada ruta. Ejecutar esa suite tras cada extracción y comprobar
  el comando de inicio documentado por el proyecto.

## H-API-10 — Calidad: payload sin modelo, excepciones amplias y lógica anidada

- **Hallazgo:** H-API-10, ahora `Resuelto` en `HALLAZGOS.md`.
- **Problema:** `create_task` toma un diccionario sin esquema; hay capturas
  generales, condicionales profundamente anidados, consultas/semillas repetidas
  y valores de configuración literales.
- **Cambio propuesto:** definir modelos Pydantic de entrada/salida que conserven
  nombres y valores por defecto observados; definir política de campos extra y
  validaciones sin cambiar silenciosamente el contrato; usar guard clauses,
  funciones de una sola responsabilidad y helpers para SQL/serialización
  repetidos; tipar identidad y respuestas; cambiar capturas amplias por
  excepciones específicas o propagación con manejo HTTP genérico. Nombrar
  constantes para valores configurables repetidos. Coordinarlo con H-API-09
  para evitar refactor duplicado.
- **Archivos api previstos:** modelos/router/servicio/repositorio bajo
  `api/app/`, `api/app/main.py` durante transición y `api/tests/test_api.py` más
  pruebas unitarias de validación.
- **Caracterización antes de tocar implementación:** registrar payloads válidos
  actuales (incluidos campos opcionales, defaults y tipos coercionados), JSON de
  respuesta y validaciones FastAPI actuales; registrar summary con estados
  TODO/DONE/ARCHIVED y prioridades observadas. Tras acordar el esquema, verificar
  respuestas válidas compatibles y errores 422 deliberados ante entradas
  inválidas, sin cambiar accidentalmente defaults o campos consumidos.
- **Ejecución real:** antes del refactor, las pruebas de defaults/coerción/campos
  extra y agregación de summary pasaron con la implementación previa. Se
  introdujeron `TaskCreateRequest` y modelos de respuesta tipados, manteniendo
  los nombres JSON y la coerción observada; se centralizaron columnas, defaults,
  configuración y semilla, y se simplificó el conteo de summary. La primera
  ejecución posterior detectó el orden invertido de `owner` y `priority` en los
  parámetros SQL; se corrigió antes de continuar. Las dos caracterizaciones
  pasaron después del arreglo. El runner oficial pasó 13 pruebas y reportó
  98,70% de cobertura global (98% en `app/main.py`), por encima del gate de 85%.
  No se cambió la forma de respuesta HTTP observada. Véase «Ejecuciones api».

## H-API-11 — Conexión SQLite compartida sin sincronización

- **Hallazgo:** H-API-11, ahora `Resuelto` en `HALLAZGOS.md` (candidato de discovery).
- **Problema:** una conexión compartida con `check_same_thread=False` se usa por
  rutas síncronas; el impacto de concurrencia estático todavía no se ha
  demostrado y debe verificarse antes de elegir una solución.
- **Cambio propuesto:** primero reproducir de forma controlada y repetible; si
  hay problemas, preferir una conexión por unidad de trabajo/request gestionada
  por el repositorio, o serializar acceso si es imprescindible mantener una
  conexión. Evitar una reescritura de persistencia sin evidencia. Migrar el
  cierre a lifespan de FastAPI si se cambia el ciclo de vida, conservando el
  cierre de recursos.
- **Archivos api previstos:** repositorio/lifecycle bajo `api/app/` y prueba de
  concurrencia aislada bajo `api/tests/`.
- **Caracterización antes de tocar implementación:** prueba controlada con
  operaciones de lectura y escritura concurrentes en base temporal, verificar
  integridad de resultados y errores; repetirla varias veces para detectar
  flakiness y registrar versión/runtime. Mantener también pruebas secuenciales
  existentes. Si no se reproduce problema, no implementar una solución
  especulativa y actualizar el estado solo con evidencia.
- **Ejecución real:** la caracterización concurrente falló antes del cambio
  con `sqlite3.InterfaceError: bad parameter or other API misuse`. Se serializó
  el acceso a la conexión compartida con `threading.Lock` y se migró su cierre
  a lifespan. Después, la prueba de 24 solicitudes concurrentes pasó cinco
  repeticiones antes y cinco después de migrar lifespan; la prueba de cierre
  también pasó. La suite completa pasó 11 pruebas con 97% de cobertura total.
  Véase «Ejecuciones api». La elección del lock es la alternativa mínima
  prevista en el plan; serializa el acceso y puede limitar throughput.

## H-API-12 — Pruebas limitadas a casos felices y un 401

- **Hallazgo:** H-API-12, `Aprobado` en `HALLAZGOS.md` (deuda de discovery).
- **Problema:** las cuatro pruebas existentes no fijan los comportamientos
  necesarios para demostrar las correcciones y podrían permitir regresiones de
  HTTP, autorización, SQL, token o carga.
- **Cambio propuesto:** ampliar pruebas por comportamiento y capa antes de cada
  refactor; reutilizar fixtures para app, base temporal, token ficticio y
  cabeceras; no duplicar casos ya cubiertos al abordar H-API-01 a H-API-11.
  Cubrir tanto éxito como bordes, errores y autorización, con cobertura de 85%
  o superior para código modificado.
- **Archivos api previstos:** `api/tests/test_api.py`, nuevos módulos de pruebas
  bajo `api/tests/` solo cuando correspondan a una capa nueva; configuración de
  pruebas únicamente si el runner existente lo requiere.
- **Caracterización antes de tocar implementación:** ejecutar la suite actual
  y conservar el resultado real como baseline; añadir pruebas de contratos de
  tareas, resumen, carga, token y backend-health antes de cambiar las rutas
  correspondientes. Asociar resultados futuros a componente `api` e IDs
  H-API-NN en el registro de ejecuciones de este plan y en `docs/TESTING.md`
  cuando se autorice ese entregable. No afirmar resultados de pruebas ni
  cobertura hasta ejecutar el comando.

## Impacto api

- **Componentes afectados:** autenticación/verificación de token, autorización,
  SQLite, cargas multipart, cliente HTTP de salud, CORS, modelos HTTP,
  organización de módulos y pruebas; todos dentro de `api/`.
- **Contratos protegidos:** endpoints y formas de éxito observadas en
  `api/app/main.py`. No hay contrato acordado para `api` en `docs/ENDPOINTS.md`.
  La autorización por identidad y el nuevo esquema de JWT pueden cambiar
  respuestas para usuarios que hoy consultan otro owner o presentan tokens
  heredados.
- **Riesgos / trade-offs:** coordinación de JWT con el servicio emisor fuera del
  alcance; reglas de rol y owner sin acuerdo; política de extensiones/tamaño y
  lista CORS de despliegue desconocidas; cambios de validación Pydantic pueden
  alterar coerciones; actualización de dependencias debe respetar compatibilidad;
  pruebas de concurrencia pueden ser inestables si no se diseñan de forma
  determinista.
- **Decisiones abiertas:** contrato del token (emisor, audiencia, algoritmo,
  llaves y transición), respuesta ante owner distinto y roles administrativos,
  extensiones/tamaño/nombre y campo `storedAt`, origen(es) CORS autorizados,
  biblioteca JWT y política de campos extra Pydantic. H-API-02, H-API-03,
  H-API-04 y H-API-08 permanecen bloqueados hasta confirmar sus respectivas
  decisiones de contrato. En la consulta de implementación del 2026-11-02 el
  usuario indicó que JWT está pendiente y no proporcionó valores para las otras
  políticas. El registro de revisión humana autoriza el alcance técnico, pero no
  sustituye los acuerdos externos necesarios.
- **Validación pendiente:** ejecutar la suite completa mediante
  `python tools/lab.py test api` desde la raíz según README.md y asociar la
  salida a cada ID que se implemente. En esta etapa se ejecutó `pytest` directo
  desde `api/` (resultados en «Ejecuciones api»); no se ejecutó auditoría de
  dependencias ni se actualizaron dependencias.

## Ejecuciones api

| fecha | componente | ID(s) | etapa | comando (cwd) | resultado |
|---|---|---|---|---|---|
| 2026-11-02 | api | H-API-01, H-API-12 | Baseline inicial | `python -m pytest --cov=app --cov-report=term-missing` (raíz; intento fuera del cwd indicado) | Falló durante collection: `ModuleNotFoundError: No module named 'app'`; no se modificó código. |
| 2026-11-02 | api | H-API-01, H-API-12 | Baseline con cwd correcto | `python -m pytest --cov=app --cov-report=term-missing` (`api/`) | Pasó: 4 pruebas; cobertura total 91%. |
| 2026-11-02 | api | H-API-01 | Caracterización antes del cambio | `python -m pytest tests/test_api.py::test_creates_task_with_apostrophes_in_text_fields -q` (`api/`) | Falló como reproducción del defecto: `sqlite3.OperationalError` al insertar texto legítimo con apóstrofos. |
| 2026-11-02 | api | H-API-01, H-API-12 | Regresión después del cambio | `python -m pytest --cov=app --cov-report=term-missing` (`api/`) | Pasó: 5 pruebas; cobertura total 91%. |
| 2026-11-02 | api | H-API-07, H-API-12 | Caracterización antes del cambio | `python -m pytest tests/test_api.py::test_invalid_token_response_does_not_expose_exception_details tests/test_api.py::test_backend_health_response_does_not_expose_exception_details -q` (`api/`) | Fallaron ambas como esperado: token inválido devolvió `Invalid token: Incorrect padding`; backend-health devolvió la excepción simulada. |
| 2026-11-02 | api | H-API-01, H-API-07, H-API-12 | Regresión después del cambio | `python -m pytest --cov=app --cov-report=term-missing` (`api/`) | Pasó: 7 pruebas; cobertura total 96%. |
| 2026-11-02 | api | H-API-05, H-API-06, H-API-12 | Caracterización ampliada en entorno global | `python -m pytest tests/test_api.py::test_upload_requires_file tests/test_api.py::test_backend_health_returns_observed_success_fields tests/test_api.py::test_uploads_requirement -q` (`api/`) | Pasó: 3 pruebas con dependencias originales. |
| 2026-11-02 | api | H-API-01, H-API-05, H-API-06, H-API-07, H-API-12 | Baseline de virtualenv antes de H-API-11 | `.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing` (`api/`) | Pasó: 9 pruebas; cobertura total 97%; se confirmaron instalados los pins originales antes de actualizarlos. |
| 2026-11-02 | api | H-API-05, H-API-06 | Caracterización antes de actualizar dependencias | `.\.venv\Scripts\python.exe -m pytest tests/test_api.py::test_upload_requires_file tests/test_api.py::test_backend_health_returns_observed_success_fields tests/test_api.py::test_uploads_requirement -q` (`api/`) | Pasó: 3 pruebas con `python-multipart 0.0.21` y `urllib3 2.5.0`. |
| 2026-11-02 | api | H-API-01, H-API-05, H-API-06, H-API-07, H-API-12 | Regresión tras actualización de dependencias | `.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing` (`api/`) | Pasó: 9 pruebas; cobertura total 97%; se verificaron instalados `python-multipart 0.0.22` y `urllib3 2.6.0`. `pip-audit` no está instalado. |
| 2026-11-02 | api | H-API-11 | Caracterización de concurrencia antes del cambio | `.\.venv\Scripts\python.exe -m pytest tests/test_api.py::test_concurrent_task_requests_preserve_sqlite_results -q` (`api/`) | Falló en la primera ejecución con `sqlite3.InterfaceError: bad parameter or other API misuse` durante consultas concurrentes. |
| 2026-11-02 | api | H-API-11 | Caracterización de cierre antes del cambio | `.\.venv\Scripts\python.exe -m pytest tests/test_api.py::test_closes_database_connection_on_shutdown -q` (`api/`) | Pasó: la conexión se cerraba al salir de TestClient; FastAPI advirtió que `on_event` está deprecado. |
| 2026-11-02 | api | H-API-11 | Verificación de lock | `1..5` ejecuciones de `.\.venv\Scripts\python.exe -m pytest tests/test_api.py::test_concurrent_task_requests_preserve_sqlite_results -q` (`api/`) | Pasaron las cinco repeticiones después de serializar acceso SQLite. |
| 2026-11-02 | api | H-API-01, H-API-05, H-API-06, H-API-07, H-API-11, H-API-12 | Suite tras H-API-11 | `.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing` (`api/`) | Pasó: 11 pruebas; cobertura total 97%; ya no aparece la advertencia deprecación de `on_event`. |
| 2026-11-02 | api | H-API-11 | Verificación final de concurrencia y lifespan | `1..5` ejecuciones de `.\.venv\Scripts\python.exe -m pytest tests/test_api.py::test_concurrent_task_requests_preserve_sqlite_results -q` (`api/`) | Pasaron las cinco repeticiones tras el cambio final de lifespan. |
| 2026-11-02 | api | H-API-01, H-API-05, H-API-06, H-API-07, H-API-11, H-API-12 | Validación con runner del proyecto | `python tools/lab.py test api` (desde la raíz; runner ejecutó pruebas en `api/`) | Pasó: 11 pruebas; cobertura total 96,77%, sobre el gate de 85%; generó `api/htmlcov/`. |
| 2026-11-02 | api | H-API-10, H-API-12 | Caracterización antes del refactor | `python -m pytest tests/test_api.py::test_create_task_preserves_current_defaults_and_string_coercion tests/test_api.py::test_summary_preserves_seeded_status_aggregation -q` (`api/`) | Pasó antes del refactor: 2 pruebas; fijó defaults, coerción string, campos extra ignorados, nombres JSON y agregación seeded de summary. |
| 2026-11-02 | api | H-API-10 | Primera regresión tras el refactor | `python -m pytest tests/test_api.py::test_create_task_preserves_current_defaults_and_string_coercion tests/test_api.py::test_summary_preserves_seeded_status_aggregation -q` (`api/`) | Falló una de dos: la prueba detectó que `priority` recibía el valor de `owner`; se corrigió el orden de los parámetros de inserción. |
| 2026-11-02 | api | H-API-10, H-API-12 | Regresión tras corregir inserción | `python -m pytest tests/test_api.py::test_create_task_preserves_current_defaults_and_string_coercion tests/test_api.py::test_summary_preserves_seeded_status_aggregation -q` (`api/`) | Pasó: 2 pruebas; defaults, coerción, forma JSON y resumen conservaron el comportamiento caracterizado. |
| 2026-11-02 | api | H-API-10 | Compilación de módulos modificados | `.\.venv\Scripts\python.exe -m py_compile app\main.py app\models.py tests\test_api.py` (`api/`) | Pasó: módulos Python compilaron sin errores. |
| 2026-11-02 | api | H-API-01, H-API-05, H-API-06, H-API-07, H-API-10, H-API-11, H-API-12 | Validación final con runner del proyecto | `python tools/lab.py test api` (desde la raíz; runner ejecutó pruebas en `api/`) | Pasó: 13 pruebas; cobertura de `app/main.py` 98% y total 98,70%, sobre el gate de 85%; generó `api/htmlcov/`. Una advertencia de deprecación proviene de `starlette.testclient` (`anyio.abc.BlockingPortal`). |
