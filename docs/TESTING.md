# Pruebas del componente web

## Alcance

Componente: **web**. Evidencia y seguimiento: **H-WEB-03** (cobertura del
flujo); las pruebas de sesión también caracterizan el comportamiento de
**H-WEB-01**. Los casos se derivan del contrato observado, no acordado, en
[`docs/ENDPOINTS.md`](./ENDPOINTS.md). Axios y el almacenamiento se simulan en
Vitest: no se llamó a los servicios HTTP reales.

## Matriz de casos

| flujo | caso | tipo | resultado esperado |
|---|---|---|---|
| Login → tareas → logout | Login válido, carga de tareas y logout | Camino feliz | Envía el body del login y el Bearer esperado; guarda token/usuario en `sessionStorage`, muestra las tareas no archivadas y al salir limpia la sesión y navega a `/login`. |
| Login | Usuario vacío o compuesto solo de espacios | Borde | No hace POST; muestra el mensaje de usuario requerido y mantiene `busy` en falso. |
| Login | Contraseña vacía o compuesta solo de espacios | Borde | No hace POST; muestra el mensaje de contraseña requerida y mantiene `busy` en falso. |
| Login | Respuesta exitosa sin token | Borde | No crea sesión ni navega; muestra que la respuesta llegó sin token. |
| Login | Servicio de autenticación no disponible | Error | Muestra el error de red, libera `busy` y no crea sesión ni navega. |
| Login | Rechazo HTTP con `response.data.message` | Error | Muestra el mensaje entregado en el error HTTP; no navega. |
| Login | Timeout configurado de 5000 ms | Error | Muestra el error de timeout, libera `busy` y no navega. |
| Dashboard | Sin token de sesión | Borde | No hace GET y navega a `/login`. |
| Dashboard | Token rechazado (fixture 401 con `detail`) | Error | Muestra `detail`, termina la carga y conserva la sesión; no redirige ni limpia el token. |
| Dashboard | Servicio de tareas no disponible | Error | Muestra el error de red y termina la carga. |
| Dashboard | Respuesta 2xx con `data` nulo | Respuesta inesperada | El `catch` muestra el mensaje de la excepción de procesamiento y termina la carga. La exposición del mensaje de excepción se registra como riesgo, no como comportamiento deseable. |
| Tareas | Estados conocidos/desconocidos | Borde | Traduce `TODO` y deja el estado desconocido sin traducir. |
| Etiqueta de tarea | Prioridad/owner ausentes o tarea ausente | Borde | Usa `NORMAL · SIN-ASIGNAR` o `SIN-DATOS`, respectivamente. |

Ubicación de los casos: `web/src/app/session/session-flow.spec.ts:40,104,124,139,155,171,189,199,216,229,241`;
`web/src/app/utils/legacy-format.spec.ts:5,9,13`.

## Código de pruebas

El código ejecutable completo, incluidos imports, mocks y fixtures, está en
[`web/src/app/session/session-flow.spec.ts`](../web/src/app/session/session-flow.spec.ts)
y [`web/src/app/utils/legacy-format.spec.ts`](../web/src/app/utils/legacy-format.spec.ts).
El camino feliz existente verifica la petición de login, la sesión, la consulta
de tareas con Bearer y el logout. Estos son los cuerpos de las pruebas añadidas
para los bordes y errores documentados:

```ts
it.each([
  { username: '  ', password: 'Workshop123!', expected: 'Ingrese un usuario' },
  { username: 'student', password: ' \t ', expected: 'Ingrese una contraseña' }
])('does not send login when required credentials are empty', async ({ username, password, expected }) => {
  const loginComponent = new LoginComponent(router, new SessionService());
  loginComponent.username = username;
  loginComponent.password = password;

  await loginComponent.login();

  expect(axios.post).not.toHaveBeenCalled();
  expect(loginComponent.message).toContain(expected);
  expect(loginComponent.busy).toBe(false);
});

it('shows the network error when the authentication service is unavailable', async () => {
  vi.mocked(axios.post).mockRejectedValue(new Error('Network Error'));
  const session = new SessionService();
  const loginComponent = new LoginComponent(router, session);
  loginComponent.username = 'student';
  loginComponent.password = 'Workshop123!';

  await loginComponent.login();

  expect(loginComponent.message).toContain('No se pudo autenticar a student.');
  expect(loginComponent.message).toContain('Network Error');
  expect(loginComponent.busy).toBe(false);
  expect(session.getToken()).toBeNull();
  expect(router.navigate).not.toHaveBeenCalled();
});

it('shows the authentication service message for a rejected login response', async () => {
  const rejection = Object.assign(new Error('Request failed with status code 401'), {
    response: { status: 401, data: { message: 'Credenciales inválidas' } }
  });
  vi.mocked(axios.post).mockRejectedValue(rejection);
  const loginComponent = new LoginComponent(router, new SessionService());
  loginComponent.username = 'student';
  loginComponent.password = 'wrong-password';

  await loginComponent.login();

  expect(loginComponent.message).toContain('Credenciales inválidas');
  expect(loginComponent.busy).toBe(false);
  expect(router.navigate).not.toHaveBeenCalled();
});

it('shows the timeout error and releases the login busy state', async () => {
  vi.mocked(axios.post).mockRejectedValue(new Error('timeout of 5000ms exceeded'));
  const loginComponent = new LoginComponent(router, new SessionService());
  loginComponent.username = 'student';
  loginComponent.password = 'Workshop123!';

  await loginComponent.login();

  expect(axios.post).toHaveBeenCalledWith(
    'http://localhost:8080/auth/login',
    { username: 'student', password: 'Workshop123!', client: 'angular-workshop' },
    { timeout: 5000 }
  );
  expect(loginComponent.message).toContain('timeout of 5000ms exceeded');
  expect(loginComponent.busy).toBe(false);
  expect(router.navigate).not.toHaveBeenCalled();
});

it('shows the invalid-token response without clearing the session or redirecting', async () => {
  const session = new SessionService();
  session.save('invalid-token', { username: 'student' });
  const rejection = Object.assign(new Error('Request failed with status code 401'), {
    response: { status: 401, data: { detail: 'Token inválido' } }
  });
  vi.mocked(axios.get).mockRejectedValue(rejection);
  const dashboard = createDashboard(router, session);

  await dashboard.ngOnInit();

  expect(dashboard.error).toBe('Token inválido');
  expect(dashboard.loading).toBe(false);
  expect(session.getToken()).toBe('invalid-token');
  expect(router.navigate).not.toHaveBeenCalled();
});

it('shows a network error when the task service is unavailable', async () => {
  const session = new SessionService();
  session.save('test-token', { username: 'student' });
  vi.mocked(axios.get).mockRejectedValue(new Error('Network Error'));
  const dashboard = createDashboard(router, session);

  await dashboard.ngOnInit();

  expect(dashboard.error).toBe('Network Error');
  expect(dashboard.loading).toBe(false);
  expect(router.navigate).not.toHaveBeenCalled();
});

it('shows the caught error when a successful task response is not an array', async () => {
  const session = new SessionService();
  session.save('test-token', { username: 'student' });
  vi.mocked(axios.get).mockResolvedValue(createAxiosResponse(null));
  const dashboard = createDashboard(router, session);

  await dashboard.ngOnInit();

  expect(dashboard.error).toContain('length');
  expect(dashboard.loading).toBe(false);
});

it('maps known task statuses and preserves an unknown status', () => {
  const dashboard = createDashboard(router, new SessionService());

  expect(dashboard.statusLabel('TODO')).toBe('Por hacer');
  expect(dashboard.statusLabel('unknown')).toBe('unknown');
});
```

La prueba de etiquetas está en
[`web/src/app/utils/legacy-format.spec.ts`](../web/src/app/utils/legacy-format.spec.ts):

```ts
it('formats priority and owner', () => {
  expect(formatTaskLabel({ priority: 'high', owner: 'student' })).toBe('HIGH · STUDENT');
});

it('uses defaults when priority and owner are absent', () => {
  expect(formatTaskLabel({})).toBe('NORMAL · SIN-ASIGNAR');
});

it('returns a fallback for an absent task', () => {
  expect(formatTaskLabel(null)).toBe('SIN-DATOS');
});
```

## Ejecuciones y resultados

Todos los comandos se ejecutaron con **cwd `web/`** y usan mocks locales. El
código de salida es el reportado por el proceso:

| componente | IDs | comando | código de salida | resultado |
|---|---|---|---:|---|
| web | H-WEB-03 | `npm run test:coverage` (línea base) | 0 | 2 archivos, 4 pruebas aprobadas; cobertura global de líneas 75,93%. |
| web | H-WEB-03 | `npm test -- src/app/session/session-flow.spec.ts src/app/utils/legacy-format.spec.ts` (primera ejecución ampliada) | 1 | 10 aprobadas y 5 fallidas; el helper de prueba `createDashboard` no tenía acceso a `router`. Se corrigió el helper para recibir el router como argumento; no fue un fallo de la aplicación. |
| web | H-WEB-03 | `npm test -- src/app/session/session-flow.spec.ts src/app/utils/legacy-format.spec.ts` (tras corregir el helper) | 0 | 2 archivos aprobados, 15 pruebas aprobadas. |
| web | H-WEB-03 | `npm run test:coverage` (resultado final) | 0 | 2 archivos aprobados, 15 pruebas aprobadas; detalle de cobertura a continuación. |
| web | H-WEB-03 | `npm run build` | 0 | Build Angular completado. Emitió advertencias CommonJS de `axios` y `lodash/merge`; no se silenciaron ni modificaron. |

### Cobertura

Método: cobertura de líneas instrumentada por Vitest con provider V8; reporte
text, `coverage-summary.json` y HTML configurados en
`web/vitest.config.ts`. Numerador y denominador corresponden a líneas cubiertas
y totales del resumen JSON:

| archivo/métrica | líneas cubiertas / totales | cobertura de líneas |
|---|---:|---:|
| `web/src/app/login/login.component.ts` | 57 / 59 | 96,61% |
| `web/src/app/dashboard/dashboard.component.ts` | 72 / 72 | 100% |
| `web/src/app/session/session.service.ts` | 20 / 20 | 100% |
| `web/src/app/utils/legacy-format.ts` | 8 / 8 | 100% |
| **Global de web** | **157 / 187** | **83,95%** |

Los cuatro archivos del flujo ejercitado superan 85% de cobertura de líneas. La
cobertura global se informa aparte; incluye el arranque y componentes/rutas no
ejercitados y no alcanza 85%. No se modificó código de producción en este paso.

## Fallos, pendientes y pruebas propuestas

### Fallos

- La primera ejecución ampliada falló en cinco pruebas por un error del helper
  de test (`router is not defined`). Se corrigió y la ejecución posterior y el
  reporte final pasaron. No quedó una prueba fallida en la última ejecución.

### Pendientes y riesgos observados

- No se ejecutó una integración con los servicios reales. Los errores HTTP,
  timeout y respuestas se representan con fixtures; el timeout prueba el
  manejo del rechazo, no espera cinco segundos ni mide la red.
- El contrato no define una respuesta de login válida sin `user`. El cliente la
  serializa sin validación y el dashboard puede fallar en `JSON.parse` antes
  del `try` (`web/src/app/session/session.service.ts:8-10`,
  `web/src/app/dashboard/dashboard.component.ts:42-43`). No se añadió una
  prueba que convierta ese comportamiento no deseado en resultado esperado;
  hace falta acordar la respuesta UI correcta antes de fijar la expectativa.
- La respuesta inesperada de tareas hace que el componente presente el mensaje
  de excepción obtenido durante el procesamiento. La prueba caracteriza ese
  camino; no valida el contenido interno como mensaje de producto ni corrige
  que se exponga el detalle técnico.
- La cobertura global de líneas es 83,95%; las métricas por archivo del flujo
  están detalladas arriba. Las advertencias CommonJS de build siguen vigentes.

### Pruebas propuestas, no ejecutadas

- Integración local con auth y API iniciados para confirmar códigos de estado,
  payloads de error, CORS y formato real de respuestas.
- Tras acordar el comportamiento de `user` ausente, añadir una prueba de
  integración login-dashboard para confirmar que no se produce una excepción
  sin manejar.
- Si se define un timeout para la consulta de tareas, agregar un caso alineado
  con ese contrato; actualmente el cliente no configura uno.
