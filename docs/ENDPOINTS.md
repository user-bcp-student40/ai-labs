# Contratos externos consumidos por web

## Alcance y estado del contrato

Este documento describe lo que el cliente Angular de `web/` envía, espera y
presenta. Es un **contrato observado en el cliente**, no una confirmación de
los servicios: en este paso no se leyó código de `auth/` ni `api/`, ni se hizo
una integración HTTP real. Los ejemplos de respuesta proceden de fixtures
locales de Vitest; no son capturas de respuestas de los backends.

**Contrato acordado:** no se encontró una confirmación del contrato con los
responsables de los servicios en las fuentes consultadas. Los códigos de
estado y los esquemas exactos del servidor permanecen pendientes de verificar.

## `POST http://localhost:8080/auth/login`

### 1. Quién lo llama

`LoginComponent` envía la solicitud al ejecutar `login()` desde el botón
«Ingresar». La llamada HTTP está directamente en el componente; después del
éxito, `SessionService` guarda el token y el usuario. La ruta `/login` carga
este componente. Evidencia: `web/src/app/login/login.component.html:34`,
`web/src/app/login/login.component.ts:31,42`,
`web/src/app/session/session.service.ts:8-10` y
`web/src/app/app.routes.ts:4-6`.

### 2. Qué envía

| Elemento | Valor observado |
|---|---|
| Método y URL | `POST http://localhost:8080/auth/login` |
| Headers explícitos | El componente no configura headers propios. Entrega un objeto como cuerpo a Axios; el header HTTP efectivo no se verificó en la red. |
| Query params | Ninguno. |
| Timeout | 5000 ms, configurado en Axios. |
| Body | Objeto JSON con `username`, `password` y `client`; el valor de `client` es `angular-workshop`. |

Evidencia: `web/src/app/login/login.component.ts:42-45`. El ejemplo coincide
con la petición esperada en el fixture local de
`web/src/app/session/session-flow.spec.ts:52-56`; usa credenciales ficticias
del laboratorio, no credenciales de producción:

```http
POST http://localhost:8080/auth/login

{
  "username": "student",
  "password": "Workshop123!",
  "client": "angular-workshop"
}
```

### 3. Qué espera recibir en éxito

Axios entrega la respuesta al flujo de éxito si la considera exitosa; el
componente no comprueba un código HTTP específico. El fixture local usa
`200`, pero eso no confirma que sea el único estado que devuelve el servicio.
El cliente comprueba que exista un `data.token` truthy; no valida el esquema de
`data.user`. Evidencia: `web/src/app/login/login.component.ts:47-50` y
`web/src/app/session/session-flow.spec.ts:37-40`.

| Campo en el cuerpo de respuesta | Uso que hace el cliente |
|---|---|
| `token` | Debe estar presente y ser truthy para guardar la sesión y navegar. Se guarda como token de sesión. |
| `user` | Se serializa y guarda sin validar su estructura. El dashboard lee `username` para el filtro de tareas y presenta `displayName` o, en su defecto, `username`. |

Evidencia: `web/src/app/session/session.service.ts:8-10`,
`web/src/app/dashboard/dashboard.component.ts:42-49` y
`web/src/app/dashboard/dashboard.component.html:6`.

Ejemplo **de fixture local**, no de respuesta capturada del backend
(`web/src/app/session/session-flow.spec.ts:37-40`):

```json
{
  "token": "test-token",
  "user": {
    "username": "student",
    "displayName": "Workshop Student"
  }
}
```

### 4. Cómo reacciona la UI ante errores o respuestas inesperadas

| Caso | Reacción observada |
|---|---|
| Usuario vacío | No envía la petición; presenta «Ingrese un usuario». |
| Contraseña vacía | No envía la petición; presenta «Ingrese una contraseña». |
| Respuesta exitosa sin token truthy | No guarda sesión ni navega; presenta «El backend respondió sin token». |
| Rechazo HTTP, incluidas credenciales inválidas si el servidor rechaza la petición | Muestra «No se pudo autenticar a <usuario>» y usa `response.data.message`; si no existe, usa `error.message` o «Error desconocido». No distingue por código de estado. |
| Timeout configurado de 5000 ms o error de red | Entra al mismo `catch` y presenta el mensaje derivado del error. El estado ocupado vuelve a falso en `finally`. |
| Token presente pero `user` ausente o inválido | No se valida antes de guardar. `SessionService` serializa el valor, y el dashboard intenta analizarlo con `JSON.parse` antes de su `try`; un valor ausente puede causar un error no manejado al entrar al dashboard. |

Evidencia: `web/src/app/login/login.component.ts:34-59`,
`web/src/app/session/session.service.ts:8-10` y
`web/src/app/dashboard/dashboard.component.ts:42-43`. El mensaje de login se
renderiza con `[innerHTML]` en
`web/src/app/login/login.component.html:39`; este comportamiento no se
considera resuelto por esta documentación.

### 5. Notas de seguridad

- El token y el usuario se guardan en `sessionStorage` bajo las claves
  `workshop_token` y `workshop_user`; el servicio los elimina al cerrar sesión.
  `sessionStorage` limita su persistencia a la sesión de la pestaña, pero sigue
  siendo accesible al JavaScript del origen. Evidencia:
  `web/src/app/session/session.service.ts:3-4,8-23`.
- El template renderiza el mensaje dinámico del login con `[innerHTML]`; el
  componente concatena el usuario y el mensaje de error recibido. No se
  inspeccionó el backend ni se verificó el renderizado en navegador.
  Evidencia: `web/src/app/login/login.component.ts:55-56` y
  `web/src/app/login/login.component.html:39`.
- El ejemplo usa datos ficticios del laboratorio. El propio formulario pide
  no utilizar credenciales reales (`web/src/app/login/login.component.html:41`).

**Preguntas abiertas:** ¿cuáles son los códigos de éxito y el esquema exacto de
error? ¿`user` y sus propiedades son obligatorios? ¿Qué headers se reciben en
una solicitud real desde el navegador?

## `GET http://localhost:8000/api/tasks?owner=<username>`

### 1. Quién lo llama

`DashboardComponent` solicita las tareas durante `ngOnInit()`, siempre que haya
un token en `SessionService`. La llamada HTTP está directamente en el
componente. La ruta `/dashboard` carga este componente. Evidencia:
`web/src/app/dashboard/dashboard.component.ts:41-50` y
`web/src/app/app.routes.ts:7-9`.

### 2. Qué envía

| Elemento | Valor observado |
|---|---|
| Método y URL | `GET http://localhost:8000/api/tasks?owner=` seguido de `user.username`; si no existe, se envía una cadena vacía. |
| Header explícito | `Authorization: Bearer <token>` obtenido de `SessionService`. |
| Body | Ninguno configurado por el componente. |
| Timeout | No se configura un timeout específico para esta solicitud. |

Evidencia: `web/src/app/dashboard/dashboard.component.ts:42-50`. El fixture
local espera esta petición con un token ficticio
(`web/src/app/session/session-flow.spec.ts:78-81`):

```http
GET http://localhost:8000/api/tasks?owner=student
Authorization: Bearer test-token
```

El `owner` se concatena a la URL sin codificación explícita; no se verificó el
comportamiento para nombres que contengan caracteres especiales.

### 3. Qué espera recibir en éxito

El componente no comprueba un código HTTP específico ni valida el esquema de
la respuesta; trata `response.data` como un arreglo. El fixture local usa
estado `200` y un arreglo de tareas. Evidencia:
`web/src/app/dashboard/dashboard.component.ts:49-60` y
`web/src/app/session/session-flow.spec.ts:65-68`.

| Campo de cada elemento usado por el cliente | Uso observado |
|---|---|
| `title` | Título mostrado en la tarjeta. |
| `description` | Descripción mostrada en la tarjeta. |
| `status` | Se muestra como estado; los elementos con estado `ARCHIVED` se excluyen de la lista visible. |
| `priority` | Se usa para formar la etiqueta y ordenar las tareas visibles. |
| `owner` | Se usa para formar la etiqueta. |

Evidencia: `web/src/app/dashboard/dashboard.component.ts:54-60`,
`web/src/app/utils/legacy-format.ts:1-9` y
`web/src/app/dashboard/dashboard.component.html:21-25`. Estos son campos que
el cliente consume, no una declaración de campos obligatorios garantizados por
el servidor.

Ejemplo **de fixture local**, no de respuesta capturada del backend
(`web/src/app/session/session-flow.spec.ts:65-68`):

```json
[
  {
    "title": "Test task",
    "description": "Local fixture",
    "status": "TODO",
    "priority": "high",
    "owner": "student"
  }
]
```

El cliente genera `label` a partir de `priority` y `owner` (para este fixture,
`HIGH · STUDENT`); no es un campo que el ejemplo del servidor necesite incluir.
Evidencia: `web/src/app/utils/legacy-format.ts:1-9`.

### 4. Cómo reacciona la UI ante errores o respuestas inesperadas

| Caso | Reacción observada |
|---|---|
| No hay token | No hace la solicitud y navega a `/login`. |
| Token inválido y respuesta HTTP no exitosa | No hay manejo específico de 401/403 ni limpieza de sesión. El `catch` muestra `response.data.detail`, si existe; en su defecto, `error.message` o «No se pudo cargar el dashboard». La sesión permanece y no se redirige por ese error. |
| Error de red o rechazo del cliente HTTP | Usa el mismo `catch`, quita el estado de carga y muestra el mensaje de error. No hay un timeout propio configurado por el componente. |
| Respuesta exitosa cuyo `data` no sea un arreglo utilizable | El procesamiento puede lanzar una excepción; el `catch` la muestra con el fallback de `error.message`. No se valida el esquema antes de recorrer los datos. |
| Arreglo con campos ausentes | No hay validación de campos. La vista puede mostrar valores vacíos o etiquetas predeterminadas; `ARCHIVED` es el único estado filtrado explícitamente. |

Evidencia: `web/src/app/dashboard/dashboard.component.ts:42-45,49-56,71-75`
y `web/src/app/dashboard/dashboard.component.html:13-27`. Los errores se
presentan mediante interpolación Angular en el párrafo de error.

### 5. Notas de seguridad

- El token se lee desde `sessionStorage` y se envía en el header Bearer;
  permanece accesible al JavaScript del origen mientras está disponible la
  sesión. Evidencia: `web/src/app/session/session.service.ts:3-4,13-18` y
  `web/src/app/dashboard/dashboard.component.ts:42,50`.
- El parámetro `owner` se envía desde el cliente como filtro. No puede
  confirmarse desde `web/` si el servicio autoriza las tareas contra la
  identidad asociada al token; el parámetro no debe considerarse evidencia de
  autorización del lado del servidor.
- Los errores de tareas se interpolan como texto en la plantilla, no mediante
  `[innerHTML]` (`web/src/app/dashboard/dashboard.component.html:18`).

**Preguntas abiertas:** ¿qué códigos de éxito/error devuelve el servicio?
¿Cuál es el esquema completo de cada tarea y de los errores? ¿Se valida en el
servidor que `owner` corresponda a la identidad del token? ¿Existe un timeout
operativo acordado para esta solicitud?
