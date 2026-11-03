# HU-01 - Token firmado con expiracion y claims minimos

## Veredicto
**Usable con ajustes.** La historia conecta seguridad, configuracion, testing y evidencia.

## Contexto
El servicio de autenticacion expone `POST /auth/login` y devuelve `token`, `expiresIn` y `user`. La implementacion usa firma HMAC y lee `AUTH_TOKEN_SECRET`.

## Ajustes necesarios
- Exigir los claims `sub`, `client`, `iat` y `exp`.
- Obtener `client` desde la solicitud, validarlo y reflejarlo en el token.
- Comprobar que `expiresIn` coincide con `exp - now` usando una tolerancia documentada.
- Eliminar el secreto por defecto fuera del laboratorio o documentarlo como exclusivo de laboratorio.
- Evitar logs del token y del secreto.
- Mantener como decision tecnica si se conserva HMAC o se adopta una libreria JWT.

## Criterios de aceptacion
- Un token valido contiene `sub`, `client`, `iat` y `exp`.
- `expiresIn` es coherente con `exp - now` dentro de la tolerancia definida.
- Login valido, credenciales invalidas y token expirado tienen pruebas.
- No se registran tokens, secretos ni valores sensibles.
- La decision sobre HMAC frente a una libreria JWT queda documentada.

## Evidencia esperada
- Documento generado por los Skills a partir de este archivo.
- Pruebas de claims, expiracion y errores de autenticacion.
- Configuracion documentada de `AUTH_TOKEN_SECRET`.
- Evidencia de logs redactados.

## API

### H-API-01 - Token de API falsificable
- Estado: CANDIDATO
- Evidencia: `api/app/main.py:26,67-73` compara un secreto fijo y decodifica un token Base64 sin verificar firma; `api/tests/test_api.py:14-16` reproduce el formato con ese mismo secreto.
- Impacto: quien conozca el formato y el secreto incluido en el código puede construir un token con cualquier usuario y rol, suplantar identidades y eludir la autenticación prevista por el contrato.
- Prioridad propuesta: P1 (alta).
- Contrato potencialmente afectado: autenticación mediante `Authorization` para todos los endpoints protegidos; formato heredado descrito en `api/openapi.json:6`.
- Cómo validarlo: crear tokens Base64 con usuario/rol distintos y comprobar si los endpoints los aceptan; añadir pruebas negativas para token alterado, firma inválida, expiración y secreto no configurado después de acordar el reemplazo del formato.

### H-API-02 - Acceso a tareas controlado por `owner` del cliente
- Estado: CANDIDATO
- Evidencia: `api/app/main.py:130-132,163-165` usa el parámetro `owner` de la solicitud para filtrar tareas y resumen sin compararlo con la identidad; `api/app/main.py:141-143` también acepta `payload.owner` al crear tareas. `api/openapi.json:15-22,129-136` expone el parámetro `owner`.
- Impacto: una identidad autenticada puede consultar tareas y agregados de otro usuario o crear tareas atribuidas a ese usuario; no se observa una comprobación de rol que autorice estas operaciones.
- Prioridad propuesta: P1 (alta).
- Contrato potencialmente afectado: aislamiento por usuario en `GET /api/tasks`, `GET /api/summary` y asignación del propietario en `POST /api/tasks`; la política de excepciones por rol aún requiere definición.
- Cómo validarlo: con dos identidades y tareas separadas, solicitar cada endpoint pasando el `owner` de la otra identidad y crear una tarea con ese `owner`; comparar el resultado con una política de autorización acordada para estudiante y roles privilegiados.

### H-API-03 - Nombre de carga permite escribir fuera del directorio de uploads
- Estado: CANDIDATO
- Evidencia: `api/app/main.py:189-192` combina `selected_uploads` directamente con `file.filename` y escribe los bytes en la ruta resultante, sin normalizar ni comprobar que permanezca dentro de `selected_uploads`. La prueba existente solo cubre un nombre ordinario: `api/tests/test_api.py:108-119`.
- Impacto: un usuario autenticado podría proporcionar un nombre con segmentos de navegación y sobrescribir archivos accesibles al proceso fuera del directorio destinado a cargas, con posible corrupción o alteración del servicio.
- Prioridad propuesta: P1 (alta).
- Contrato potencialmente afectado: `POST /api/requirements` multipart y su respuesta `fileName`/`storedAt`; nombres permitidos y política de sobrescritura no están definidos en el contrato revisado.
- Cómo validarlo: en un directorio temporal, probar nombres con `..`, rutas absolutas y separadores de ambos sistemas; comprobar que no se crea ni sobrescribe ningún archivo fuera del directorio de cargas y que la API responde con el error acordado.

### H-API-04 - Carga de archivos sin límite de tamaño visible
- Estado: APROBADO
- Evidencia: `api/app/main.py:191-192` lee el archivo completo a memoria con `await file.read()` y lo escribe sin comprobar tamaño; `api/tests/test_api.py:108-127` solo cubre una carga pequeña y la ausencia del campo. No se encontró una cuota en la ruta ni en los modelos revisados.
- Impacto: cargas grandes pueden consumir memoria y espacio temporal/disco del servicio y degradar su disponibilidad; no hay un rechazo por tamaño máximo observable en este flujo.
- Prioridad propuesta: P2 (media).
- Contrato potencialmente afectado: límites y errores de `POST /api/requirements`; el tamaño máximo y la respuesta para exceso deben acordarse antes de fijar el comportamiento.
- Cómo validarlo: acordar un límite, enviar archivos en el límite y por encima de él y verificar aceptación/rechazo determinista (por ejemplo, 413) y que el uso de recursos no crezca con una lectura completa sin control.