# Limitar el tamaño de archivos cargados en la API

## Fuente
Hallazgo H-API-04 — Carga de archivos sin límite de tamaño visible.

- Evidencia: `api/app/main.py:191-192` lee el archivo completo a memoria y lo escribe sin comprobar tamaño; `api/tests/test_api.py:108-127` solo cubre una carga pequeña y la ausencia del campo. No se encontró una cuota en la ruta ni en los modelos revisados.
- Impacto: cargas grandes pueden consumir memoria y espacio temporal o de disco del servicio y degradar su disponibilidad.

## Contexto actual
`POST /api/requirements` recibe un archivo multipart, lo lee completo y, tras guardarlo, responde con estado `201` y los campos `owner`, `fileName`, `storedAt` y `size`. No se observa un límite de tamaño definido en el flujo revisado.

## Problema confirmado
El contrato no define un tamaño máximo ni el comportamiento ante una carga que lo exceda. Por tanto, el servicio no presenta un rechazo por tamaño máximo observable en este flujo.

## Comportamiento a preservar
- Mantener `POST /api/requirements` y el campo multipart `file`.
- Para cargas aceptadas, conservar el estado `201` y los campos de respuesta `owner`, `fileName`, `storedAt` y `size`.
- Conservar el rechazo actual cuando falta el archivo.
- Aceptar archivos de hasta 10,000,000 bytes inclusive; rechazar archivos mayores con estado `400` y cuerpo `{"detail":"File exceeds maximum size"}`.
- No cambiar los contratos de `POST /auth/login` ni de `/api/tasks`.

## Alcance
- Aplicar un límite de 10,000,000 bytes por archivo en el endpoint.
- Rechazar el exceso antes de persistirlo y sin leerlo completo en la memoria de la aplicación.
- Documentar el límite y la respuesta `400` en el contrato de la API.

## Fuera de alcance
- Cambiar nombres de endpoints, el formato de respuestas exitosas o la ubicación de almacenamiento.
- Definir reglas de nombre, extensión o contenido de archivos.
- Refactorizar la estructura interna del servicio.

## Criterios de aceptación
1. El límite máximo de archivo es 10,000,000 bytes y está documentado.
2. Una carga de hasta el límite se acepta y su respuesta conserva el contrato de éxito; `size` coincide con el tamaño real del archivo en bytes.
3. Una carga que excede el límite se rechaza con estado `400` y cuerpo `{"detail":"File exceeds maximum size"}`; no se guarda ni se responde con `201`.
4. La prueba de límite cubre 10,000,000 y 10,000,001 bytes.
5. La ausencia del campo `file` conserva el comportamiento documentado.
6. Los contratos protegidos indicados en esta spec permanecen sin cambios.

## Contratos afectados/protegidos
- **Afectado:** `POST /api/requirements`, multipart con `file`. El éxito es `201` con `owner`, `fileName`, `storedAt` y `size`; los archivos mayores a 10,000,000 bytes responden `400` con `{"detail":"File exceeds maximum size"}`. La especificación OpenAPI está en `api/openapi.json`.
- **Protegidos:** `POST /auth/login` y `/api/tasks`; esta especificación no autoriza cambios a esos endpoints ni a sus formatos.

## Riesgos, supuestos y preguntas abiertas
- El límite se aplica por archivo en el endpoint. El parseo multipart puede utilizar almacenamiento temporal antes de que el endpoint rechace el exceso; limitar el cuerpo en infraestructura queda fuera de esta decisión.
- No quedan decisiones abiertas para el alcance aprobado.
