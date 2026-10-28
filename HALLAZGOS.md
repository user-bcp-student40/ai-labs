# Hallazgos

## Contrato observado de web

`docs/ENDPOINTS.md` documenta el contrato observado por el frontend; no confirma
los contratos de los servicios ni una integración real. El flujo que se observa
en el código es:

1. La ruta `/login` carga `LoginComponent`; la ruta raíz y las rutas desconocidas redirigen a `/login` (`web/src/app/app.routes.ts:5,6,12,13`).
2. El componente valida que usuario y contraseña no estén vacíos y envía `POST http://localhost:8080/auth/login` con `username`, `password` y `client: 'angular-workshop'` (`web/src/app/login/login.component.ts:32,33,36,41,42,43,44`).
3. Si la respuesta contiene token, la sesión guarda token y usuario en `sessionStorage`; las preferencias siguen en `localStorage`, y el componente navega a `/dashboard` (`web/src/app/login/login.component.ts:48,49`; `web/src/app/session/session.service.ts:8,9,10`).
4. El dashboard lee token y usuario de la sesión; sin token vuelve a `/login`. Con token solicita `GET http://localhost:8000/api/tasks?owner=<username>` y envía el token en la cabecera `Authorization` (`web/src/app/dashboard/dashboard.component.ts:42,43,44,45,49,50`; `web/src/app/session/session.service.ts:13,14,17,18`).
5. Cerrar sesión borra token y usuario de la sesión y navega a `/login` (`web/src/app/dashboard/dashboard.component.ts:80,81,82`; `web/src/app/session/session.service.ts:21,22,23`).

Esto describe el contrato observado por el cliente, no un contrato acordado ni
una integración verificada. Las pruebas locales con mocks y sus resultados se
registran en `docs/TESTING.md`; no se leyó código de otros componentes ni se
ejecutaron solicitudes reales a los servicios.

## Matriz de seguimiento — web

| id | componente | hallazgo | tipo | explicacion | evidencia (archivo:linea) | severidad | estado |
|---|---|---|---|---|---|---|---|
| H-WEB-01 | web | Token de sesión almacenado en `localStorage` | Vulnerabilidad | Resuelto: token y usuario se centralizaron en `SessionService` y migraron a `sessionStorage`; las preferencias permanecen en `localStorage`. `sessionStorage` sigue accesible al JavaScript del origen mientras la pestaña está abierta, por lo que no es una mitigación completa frente a XSS. | `web/src/app/session/session.service.ts:3,4,8,9,10,13,14,17,18,21,22,23`; `web/src/app/login/login.component.ts:48`; `web/src/app/dashboard/dashboard.component.ts:42,43,81` | media | Resuelto |
| H-WEB-02 | web | Mensaje dinámico mostrado con `[innerHTML]` | Vulnerabilidad | El mensaje incorpora el usuario y un texto proveniente del error, y se presenta en contexto HTML. Angular sanitiza normalmente este contexto; con la lectura estática no se demuestra ejecución de contenido ni se verificó el resultado en navegador. | `web/src/app/login/login.component.ts:55,56`; `web/src/app/login/login.component.html:39` | media | Pendiente |
| H-WEB-03 | web | Cobertura de pruebas del flujo de login y dashboard incompleta | Refactor | Se añadió caracterización del login exitoso y sin token, dashboard con y sin token, consulta con cabecera Bearer y logout como parte de H-WEB-01. Siguen sin cobertura dedicada validaciones vacías, rechazos HTTP y otros estados de error; H-WEB-03 permanece pendiente. | `web/src/app/session/session-flow.spec.ts:35,92,112`; `web/src/app/utils/legacy-format.spec.ts:4,5,6` | media | Pendiente |
| H-WEB-04 | web | Componentes concentran llamadas HTTP, configuración de URL, sesión y navegación | Refactor | Login y dashboard aún realizan llamadas Axios directamente y conocen sus URLs; la lectura/escritura de token y usuario ya se delega a `SessionService` como resolución acotada de H-WEB-01. La separación de HTTP y configuración sigue pendiente. | `web/src/app/login/login.component.ts:42,43,44,48,50`; `web/src/app/dashboard/dashboard.component.ts:42,43,49,50,80,81,82` | baja | Pendiente |
| H-WEB-05 | web | Dependencias `axios` y `lodash` en las versiones candidatas del reto | Sugerencia | El manifiesto declara las versiones señaladas por `RETO.md`. La presencia queda confirmada; no se consultaron advisories ni se confirmó un CVE, por lo que el riesgo de seguridad de esas versiones sigue pendiente de evaluación. | `web/package.json:19-20`; uso de Axios y Lodash: `web/src/app/login/login.component.ts:5-6` | baja | Pendiente |
| H-WEB-06 | web | Uso de `any` y validación anidada en el flujo de login | Refactor | El tipado `any` elimina comprobaciones estáticas en estado y respuesta; las validaciones anidadas hacen menos directo el flujo ante campos vacíos. | `web/src/app/login/login.component.ts:17,18,19,20,21,34,37,42,54`; `web/src/app/dashboard/dashboard.component.ts:24,25,26,27,28,43,49,53,60,71` | baja | Pendiente |
| H-WEB-07 | web | Duplicación de bloques de código | Refactor | No se identificó un bloque duplicado concreto en el código de `web/` revisado. Las responsabilidades HTTP/sesión repetidas entre componentes se registran en H-WEB-04, pero no bastan por sí solas para confirmar duplicación de código. | Áreas revisadas: `web/src/app/login/login.component.ts:31,59`; `web/src/app/dashboard/dashboard.component.ts:35,77` | baja | No encontrado |

### Actualización de seguimiento — H-WEB-03

La fila de H-WEB-03 conserva el estado anterior a la ampliación de pruebas.
`docs/TESTING.md` registra que ya se cubren credenciales vacías, respuestas sin
token, errores HTTP/red, timeout, token inválido y respuesta inesperada de
tareas. El hallazgo permanece `Pendiente` porque el contrato no define el
resultado UI ante un login con token pero sin `user`; no se convirtió el bug
observado en comportamiento esperado por una prueba. La cobertura, comandos y
resultados reales están en `docs/TESTING.md`. Casos: `web/src/app/session/session-flow.spec.ts:40,104,124,139,155,171,189,199,216,229,241`;
etiquetas: `web/src/app/utils/legacy-format.spec.ts:5,9,13`.

## Candidatos de discovery — web

### H-WEB-08 — Error no controlado si la respuesta de login omite `user`
- Estado: CANDIDATO
- Evidencia: `web/src/app/login/login.component.ts:47-49` guarda `response.data.user` si existe un token; `web/src/app/session/session.service.ts:8-10` serializa el usuario; `web/src/app/dashboard/dashboard.component.ts:42-43` analiza el valor de sesión antes del bloque `try`.
- Impacto: si `user` está ausente, su serialización puede almacenarse como el texto `undefined`; el dashboard puede fallar en `JSON.parse` antes de manejar el error, interrumpiendo el flujo posterior al login.
- Prioridad propuesta: Media (P2), por el impacto funcional condicionado a una respuesta incompleta o sesión alterada.
- Contrato potencialmente afectado: respuesta de `POST /auth/login` y datos de sesión requeridos por el dashboard; el contrato observado no define si `user` es obligatorio.
- Cómo validarlo: agregar pruebas con respuesta de login con token y sin `user`, y con valor de usuario inválido almacenado; comprobar que el resultado acordado se maneje sin excepción no controlada.

### H-WEB-09 — Valor `owner` concatenado directamente en la URL de tareas
- Estado: CANDIDATO
- Evidencia: `web/src/app/dashboard/dashboard.component.ts:49` concatena `this.user.username` directamente en `?owner=`; `web/src/app/session/session-flow.spec.ts:87` solo caracteriza el nombre simple `student`.
- Impacto: si se admite un nombre de usuario con caracteres reservados de URL, el filtro puede interpretarse como parámetros distintos y no representar el usuario esperado.
- Prioridad propuesta: Baja (P3), condicionada a los caracteres permitidos por el contrato de identidad.
- Contrato potencialmente afectado: parámetro `owner` de `GET /api/tasks`; no está confirmado el conjunto permitido de caracteres.
- Cómo validarlo: acordar los caracteres válidos para `username` y probar nombres con caracteres reservados; verificar que la solicitud codifique el valor y que el servicio reciba el `owner` esperado.

### H-WEB-10 — Respuesta 401 conserva la sesión y no redirige
- Estado: CANDIDATO
- Evidencia: `web/src/app/dashboard/dashboard.component.ts:67-75` muestra el error sin limpiar sesión ni navegar; `web/src/app/session/session-flow.spec.ts:199-213` caracteriza explícitamente que ante 401 se conserva el token y no se redirige.
- Impacto: una sesión con token rechazado permanece en el almacenamiento y puede provocar solicitudes fallidas repetidas; no se ha confirmado si el servicio usa 401 para indicar sesión inválida o si el comportamiento actual es intencional.
- Prioridad propuesta: Media (P2), pendiente de confirmar el significado contractual del 401.
- Contrato potencialmente afectado: manejo de autenticación y errores de `GET /api/tasks`, además del ciclo de vida de sesión en web.
- Cómo validarlo: confirmar con responsables del servicio el significado de 401 y el resultado esperado para la sesión; ajustar o conservar la prueba existente según la decisión y verificar que el flujo final cumpla el contrato.
