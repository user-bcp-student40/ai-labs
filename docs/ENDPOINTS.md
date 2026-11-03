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

## Contrato de la API FastAPI (`api`)

### Alcance y estado del contrato

Esta sección describe el contrato observado en `api/app/main.py` y los modelos
Pydantic de `api/app/models.py`. No se encontró una confirmación humana de un
contrato acordado para `api`; los ejemplos reflejan la implementación actual,
no una garantía de compatibilidad futura. Las respuestas HTTP completas de
errores internos dependen del servidor y su configuración, por lo que solo se
documentan aquí los errores cuyo comportamiento puede verificarse en el código.

Todos los endpoints requieren el header exacto `Authorization` con un valor
que actualmente se procesa como `Bearer <token>`. El token que entiende el
código actual no es JWT: es Base64 del texto
`username|role|expiry-unix|WORKSHOP_SECRET_2026`. Para obtener un ejemplo válido
con expiración futura, el siguiente helper genera el header para los ejemplos
de esta sección:

```python
import base64
import time

def example_headers():
    raw = f"student|STUDENT|{int(time.time()) + 3600}|WORKSHOP_SECRET_2026"
    token = base64.b64encode(raw.encode("utf-8")).decode("ascii")
    return {"Authorization": f"Bearer {token}"}
```

El secreto fijo y el formato sin firma son riesgos pendientes, no una
recomendación para despliegues. El código reemplaza literalmente `Bearer `
antes de decodificar y no valida estrictamente el esquema del header.

### `GET /api/tasks`

#### 1. Qué hace

Devuelve las tareas registradas para el `owner` solicitado, ordenadas por ID
ascendente; si el parámetro no se envía o está vacío, usa el usuario del token.

#### 2. Autenticación

Requiere `Authorization: Bearer <token>` según el helper anterior. Un token
inválido produce `401`.

#### 3. Request

No tiene body.

| Campo/parametro | Tipo | Obligatorio | Descripcion |
|---|---|---|---|
| `owner` (query) | string | No | Owner por el que filtrar. Si falta o es cadena vacía, se usa `username` del token. La implementación actual permite especificar otro owner. |
| `Authorization` (header) | string | Sí | Header de autenticación; formato esperado para el ejemplo: `Bearer <token>` generado arriba. |

Ejemplo completo (header calculado con `example_headers()`):

```http
GET /api/tasks?owner=student HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token generado por example_headers()>
```

#### 4. Response exitosa

Código HTTP: `200 OK`. Devuelve un arreglo; puede estar vacío.

| Campo | Tipo | Descripcion |
|---|---|---|
| `id` | integer | Identificador de la tarea. |
| `title` | string | Título. |
| `description` | string | Descripción. |
| `status` | string | Estado almacenado. |
| `owner` | string | Propietario almacenado. |
| `priority` | string | Prioridad almacenada. |
| `createdAt` | string | Fecha y hora asignadas por SQLite con `datetime('now')`. |

Ejemplo de respuesta con las tareas `student` sembradas al iniciar una base
vacía (la base puede cambiar después de crear tareas):

```json
[
  {
    "id": 1,
    "title": "Refactor login",
    "description": "Separar responsabilidades en frontend",
    "status": "TODO",
    "owner": "student",
    "priority": "HIGH",
    "createdAt": "2026-11-02 22:00:00"
  },
  {
    "id": 2,
    "title": "Review API",
    "description": "Revisar seguridad de endpoints",
    "status": "IN_PROGRESS",
    "owner": "student",
    "priority": "MEDIUM",
    "createdAt": "2026-11-02 22:00:00"
  }
]
```

Las fechas del ejemplo ilustran el formato, no son valores fijos; SQLite
genera la hora al insertar cada fila.

#### 5. Respuestas de error

| Codigo HTTP | Cuando ocurre | Ejemplo de cuerpo |
|---|---|---|
| `401 Unauthorized` | Header ausente, token malformado, expirado o con secreto/formato no aceptado. | `{"detail":"Invalid token"}` |
| `500 Internal Server Error` | Error interno no manejado al acceder a SQLite o serializar la respuesta. El cuerpo exacto depende de FastAPI/servidor y configuración. | `{"detail":"Internal Server Error"}` |

El parámetro `owner` es un string y no se observó una respuesta 422 propia de
validación para esta ruta.

#### 6. Notas de seguridad

- El query `owner` no está restringido a la identidad del token; un cliente
  autenticado puede pedir otro owner. La autorización por identidad está
  pendiente de decisión/corrección.
- Las consultas usan parámetros SQL para el valor de `owner`; esto evita que el
  valor se interprete como SQL, pero no sustituye la autorización.
- El token Base64 no tiene firma criptográfica y usa un secreto fijo. No debe
  tratarse como autenticación robusta.

### `POST /api/tasks`

#### 1. Qué hace

Crea una tarea con los campos recibidos y devuelve la fila creada.

#### 2. Autenticación

Requiere `Authorization: Bearer <token>` según el helper de autenticación de
esta sección. Un token inválido produce `401`.

#### 3. Request

El body es JSON. Todos los campos del modelo tienen defaults; los campos
desconocidos se ignoran. Los valores recibidos para `title`, `description`,
`status`, `priority` y `owner` se convierten a string, incluso si el JSON
contiene `null`.

| Campo/parametro | Tipo | Obligatorio | Descripcion |
|---|---|---|---|
| `title` | string | No | Título; default `""`. |
| `description` | string | No | Descripción; default `""`. |
| `status` | string | No | Estado; default `"TODO"`. |
| `priority` | string | No | Prioridad; default `"MEDIUM"`. |
| `owner` | string o null | No | Owner para la nueva fila; si se omite o es null, se usa `username` del token. Actualmente un valor no nulo enviado por el cliente se acepta. |
| `Authorization` (header) | string | Sí | Header de autenticación; formato esperado para el ejemplo: `Bearer <token>` generado arriba. |

Ejemplo completo:

```http
POST /api/tasks HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token generado por example_headers()>
Content-Type: application/json

{
  "title": "Review requirements",
  "description": "Check acceptance criteria",
  "status": "TODO",
  "priority": "HIGH"
}
```

#### 4. Response exitosa

Código HTTP: `201 Created`.

| Campo | Tipo | Descripcion |
|---|---|---|
| `id` | integer | Identificador de la nueva tarea. |
| `title` | string | Título almacenado (tras coerción a string). |
| `description` | string | Descripción almacenada (tras coerción a string). |
| `status` | string | Estado almacenado. |
| `owner` | string | Owner almacenado; por defecto es el username del token. |
| `priority` | string | Prioridad almacenada. |
| `createdAt` | string | Fecha y hora asignadas por SQLite. |

Ejemplo de respuesta para el request anterior en una base nueva con las tres
filas semilla:

```json
{
  "id": 4,
  "title": "Review requirements",
  "description": "Check acceptance criteria",
  "status": "TODO",
  "owner": "student",
  "priority": "HIGH",
  "createdAt": "2026-11-02 22:00:00"
}
```

El ID y la fecha dependen del contenido de la base y del momento de la
inserción; el ejemplo muestra la forma de respuesta.

#### 5. Respuestas de error

| Codigo HTTP | Cuando ocurre | Ejemplo de cuerpo |
|---|---|---|
| `401 Unauthorized` | Header ausente, token malformado, expirado o con secreto/formato no aceptado. | `{"detail":"Invalid token"}` |
| `422 Unprocessable Entity` | JSON malformado o body que no sea un objeto compatible con el modelo. Los campos del objeto no son obligatorios; sus valores se convierten a string. | `{"detail":[{"type":"json_invalid","loc":["body",1],"msg":"JSON decode error","input":{},"ctx":{"error":"Expecting property name enclosed in double quotes"}}]}` |
| `500 Internal Server Error` | Error interno no manejado durante la inserción, commit o consulta. El cuerpo exacto depende de FastAPI/servidor y configuración. | `{"detail":"Internal Server Error"}` |

#### 6. Notas de seguridad

- `owner` puede ser enviado por el cliente y se guarda si no es null; el endpoint
  no comprueba que coincida con la identidad del token. Autorización pendiente.
- Los valores SQL se insertan mediante parámetros.
- La autenticación sigue usando el formato Base64 heredado y secreto fijo
  descrito al inicio de esta sección.

### `GET /api/summary`

#### 1. Qué hace

Devuelve el total de tareas, la cantidad agrupada por estado y las tareas
abiertas de prioridad alta para un owner.

#### 2. Autenticación

Requiere `Authorization: Bearer <token>` según el helper de autenticación de
esta sección. Un token inválido produce `401`.

#### 3. Request

No tiene body.

| Campo/parametro | Tipo | Obligatorio | Descripcion |
|---|---|---|---|
| `owner` (query) | string | No | Owner por el que resumir; si falta o es cadena vacía, usa `username` del token. La implementación actual permite especificar otro owner. |
| `Authorization` (header) | string | Sí | Header de autenticación; formato esperado para el ejemplo: `Bearer <token>` generado arriba. |

Ejemplo completo:

```http
GET /api/summary?owner=student HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token generado por example_headers()>
```

#### 4. Response exitosa

Código HTTP: `200 OK`.

| Campo | Tipo | Descripcion |
|---|---|---|
| `owner` | string | Owner del que se calculó el resumen. |
| `total` | integer | Número total de tareas del owner. |
| `byStatus` | objeto de string a integer | Conteo de tareas agrupado por `status`. |
| `highPriorityOpen` | integer | Tareas con `priority == "HIGH"` cuyo status no es `DONE` ni `ARCHIVED`. |

Ejemplo con la base vacía recién inicializada y sus tareas semilla:

```json
{
  "owner": "student",
  "total": 2,
  "byStatus": {
    "TODO": 1,
    "IN_PROGRESS": 1
  },
  "highPriorityOpen": 1
}
```

#### 5. Respuestas de error

| Codigo HTTP | Cuando ocurre | Ejemplo de cuerpo |
|---|---|---|
| `401 Unauthorized` | Header ausente, token malformado, expirado o con secreto/formato no aceptado. | `{"detail":"Invalid token"}` |
| `500 Internal Server Error` | Error interno no manejado durante la consulta o el cálculo. El cuerpo exacto depende de FastAPI/servidor y configuración. | `{"detail":"Internal Server Error"}` |

El parámetro `owner` es un string y no se observó una respuesta 422 propia de
validación para esta ruta.

#### 6. Notas de seguridad

- El cliente puede seleccionar un `owner` distinto al username del token; no hay
  autorización por rol o identidad en esta ruta.
- La consulta parametriza el owner, pero parametrización no equivale a
  autorización.
- El cálculo considera `HIGH` como prioridad alta y excluye `DONE` y
  `ARCHIVED` de las tareas abiertas.

### `POST /api/requirements`

#### 1. Qué hace

Guarda en el directorio configurado una especificación de requerimiento enviada
como archivo y devuelve metadatos de la carga.

#### 2. Autenticación

Requiere `Authorization: Bearer <token>` según el helper de autenticación de
esta sección. Un token inválido produce `401`.

#### 3. Request

El body es `multipart/form-data`; el campo `file` es obligatorio.

| Campo/parametro | Tipo | Obligatorio | Descripcion |
|---|---|---|---|
| `file` | archivo (`UploadFile`) | Sí | Contenido que se guarda; el nombre enviado se usa directamente como nombre de archivo. |
| `Authorization` (header) | string | Sí | Header de autenticación; formato esperado para el ejemplo: `Bearer <token>` generado arriba. |

Ejemplo completo, con un archivo ficticio:

```http
POST /api/requirements HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token generado por example_headers()>
Content-Type: multipart/form-data; boundary=example-boundary

--example-boundary
Content-Disposition: form-data; name="file"; filename="requirements.txt"
Content-Type: text/plain

The login form must display a generic error.
--example-boundary--
```

#### 4. Response exitosa

Código HTTP: `201 Created`.

| Campo | Tipo | Descripcion |
|---|---|---|
| `owner` | string | Username del token. |
| `fileName` | string | Nombre enviado por el cliente. |
| `storedAt` | string | Ruta del archivo guardado; depende del directorio configurado y del sistema operativo. |
| `size` | integer | Tamaño del contenido en bytes. |

Ejemplo para `requirements.txt` guardado con el directorio predeterminado
`./uploads` en Windows:

```json
{
  "owner": "student",
  "fileName": "requirements.txt",
  "storedAt": "uploads\\requirements.txt",
  "size": 43
}
```

El campo `storedAt` puede variar por configuración y sistema operativo; el
ejemplo de bytes corresponde al texto mostrado en el request.

#### 5. Respuestas de error

| Codigo HTTP | Cuando ocurre | Ejemplo de cuerpo |
|---|---|---|
| `401 Unauthorized` | Header ausente, token malformado, expirado o con secreto/formato no aceptado. | `{"detail":"Invalid token"}` |
| `422 Unprocessable Entity` | No se envía el campo requerido `file` o la solicitud multipart no puede validarse. | `{"detail":[{"type":"missing","loc":["body","file"],"msg":"Field required","input":null}]}` |
| `500 Internal Server Error` | Error no manejado al escribir el archivo, por ejemplo, permisos o ruta inválida. El cuerpo exacto depende de FastAPI/servidor y configuración. | `{"detail":"Internal Server Error"}` |

#### 6. Notas de seguridad

- El código usa el filename del cliente sin normalizarlo, no aplica límite de
  tamaño ni extensión y lee el archivo completo en memoria antes de escribir.
- Un nombre repetido puede sobrescribir el archivo anterior; no se valida la
  ruta final contra el directorio de carga.
- La respuesta expone la ruta almacenada. Estas políticas de carga segura están
  pendientes.

### `GET /api/backend-health`

#### 1. Qué hace

Consulta el endpoint de salud de un backend configurado y devuelve el usuario
que solicitó la consulta, el estado recibido y el cuerpo recibido.

#### 2. Autenticación

Requiere `Authorization: Bearer <token>` según el helper de autenticación de
esta sección. Un token inválido produce `401`.

#### 3. Request

No tiene body ni parámetros de ruta o query.

| Campo/parametro | Tipo | Obligatorio | Descripcion |
|---|---|---|---|
| `Authorization` (header) | string | Sí | Header de autenticación; formato esperado para el ejemplo: `Bearer <token>` generado arriba. |
| `AUTH_HEALTH_URL` (configuración del servidor) | URL string | No | No es un campo del request. Define el destino; si no está configurada, el código usa `http://localhost:8080/q/health`. |

Ejemplo completo:

```http
GET /api/backend-health HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token generado por example_headers()>
```

#### 4. Response exitosa

Código HTTP: `200 OK` cuando la ruta retorna un modelo, incluso si la consulta
al backend falla. El estado del backend se devuelve en el campo JSON `status`;
no es necesariamente el estado HTTP de esta respuesta.

| Campo | Tipo | Descripcion |
|---|---|---|
| `requestedBy` | string | Username del token. |
| `status` | integer | Código HTTP recibido del backend, o `0` si ocurre una excepción de las capturadas. |
| `body` | string | Cuerpo UTF-8 recibido, o mensaje genérico si ocurre una excepción de las capturadas. |

Ejemplo cuando el backend responde HTTP 200 con el cuerpo `healthy`:

```json
{
  "requestedBy": "student",
  "status": 200,
  "body": "healthy"
}
```

Ejemplo de fallo controlado del backend (la respuesta HTTP de esta ruta sigue
siendo `200 OK`):

```json
{
  "requestedBy": "student",
  "status": 0,
  "body": "Backend health check failed"
}
```

#### 5. Respuestas de error

| Codigo HTTP | Cuando ocurre | Ejemplo de cuerpo |
|---|---|---|
| `401 Unauthorized` | Header ausente, token malformado, expirado o con secreto/formato no aceptado. | `{"detail":"Invalid token"}` |
| `500 Internal Server Error` | Error no manejado fuera de las excepciones de red/decodificación capturadas. El cuerpo exacto depende de FastAPI/servidor y configuración. | `{"detail":"Internal Server Error"}` |

Un error de red HTTP, error de sistema operativo o cuerpo no UTF-8 no genera
un error HTTP de esta ruta: se captura y se devuelve el objeto con `status: 0`
descrito arriba. Los códigos 4xx/5xx del backend consultado se incluyen en el
campo `status`, mientras la respuesta de esta ruta sigue con HTTP 200.

#### 6. Notas de seguridad

- `AUTH_HEALTH_URL` controla el destino de la solicitud saliente; proteger su
  configuración y limitarla a destinos de confianza. El código no valida
  esquema, host ni destino.
- El timeout de solicitud configurado es de 3 segundos.
- Los errores capturados se registran en el servidor; el cuerpo de respuesta
  controlado es genérico.
- La autenticación de esta ruta usa el mismo token Base64 sin firma descrito
  al inicio.

### Contratos pendientes de confirmar (`api`)

- Sustituir/coordinar el formato heredado del token con un emisor que acuerde
  algoritmo, firma, issuer, audience, expiración y transición.
- Definir si `owner` puede consultarse/crearse distinto a la identidad y qué
  roles, si alguno, pueden hacerlo.
- Definir extensiones permitidas, tamaño máximo, normalización, sobrescritura y
  formato de `storedAt` para archivos.
- Acordar orígenes CORS permitidos.
- Confirmar qué errores HTTP internos y de infraestructura desea considerar
  parte del contrato; los ejemplos 500 anteriores describen el comportamiento
  estándar cuando FastAPI no captura una excepción, no un esquema de error
  personalizado.
