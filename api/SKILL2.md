---
name: businesspath-explorer
description: Analiza endpoints OpenAPI, explora caminos de negocio y genera preguntas priorizadas para detectar vacíos e inconsistencias antes de implementar.
---

# Skill: BusinessPath Explorer

## 1) Metadata

- **Skill ID:** businesspath-explorer
- **Version:** 0.1.0
- **Purpose:** Analizar uno o varios endpoints definidos en OpenAPI,
  explorar sus caminos de negocio e identificar preguntas, vacíos
  y posibles inconsistencias antes de su implementación.
- **Audience (roles):** Product Owner, analista de negocio, Arquitectura,
  Tech Lead, Backend y QA.
- **When to use:** Antes de implementar, modificar o aprobar endpoints
  cuyo comportamiento de negocio necesita aclaración.
- **When NOT to use:** Para implementar código, certificar cumplimiento
  BIAN o realizar una auditoría técnica completa de seguridad.
- **Sensitive inputs:** No incluyas datos reales de clientes,
  credenciales, secretos, tokens ni URLs internas no autorizadas.
- **Expected output:** Informe Markdown con escenarios de negocio,
  preguntas priorizadas, análisis del contrato y criterios de aceptación.

## 2) Inputs

Proporciona, cuando estén disponibles:

- **OpenAPI contract:** Ruta o contenido del archivo YAML o JSON.
- **Endpoints in scope:** Métodos y rutas que se desean analizar.
- **Business context:** Objetivo de la API y proceso de negocio.
- **Business rules:** Reglas, restricciones y decisiones ya acordadas.
- **Examples:** Solicitudes, respuestas y escenarios con datos ficticios.
- **BIAN reference:** Versión, servicio, operación y documento o enlace
  específico con el que se desea comparar el contrato.
- **Existing documentation:** Historias de usuario, criterios de aceptación
  y documentos de negocio relevantes.
- **Audience:** Responsables que responderán las preguntas.

Si no se indica el alcance, pregunta si se deben analizar todos los
endpoints del contrato. Si faltan reglas o contexto, continúa con el
contrato disponible e identifica la información faltante como pregunta.

## 3) Output

Devuelve un informe Markdown con las siguientes secciones:

1. **Summary**
   - Objetivo, alcance y fuentes revisadas.
   - Limitaciones del análisis.

2. **Endpoint Inventory**
   - Tabla: método | ruta | propósito declarado | entidades involucradas.

3. **Contract Validation**
   - Resultado de la validación OpenAPI y referencias revisadas.
   - Problemas que impidan comprender o evaluar el contrato.
   - Comprobaciones no realizadas y sus motivos.

4. **BIAN Alignment**
   - Referencia BIAN utilizada, incluida su versión.
   - Correspondencias y diferencias verificadas.
   - Aspectos no comprobados por falta de referencia o acceso.
   - No declares una certificación de cumplimiento.

5. **Known Business Rules**
   - Reglas explícitas con su fuente.
   - Comportamientos inferidos, separados de los requisitos confirmados.

6. **Business Path Matrix**
   - Caminos de negocio identificados para cada endpoint.
   - Condiciones que originan cada camino.
   - Resultado definido o decisión pendiente.
   - Estado: definido, ambiguo o no comprobado.

7. **Business Questions**
   - Preguntas agrupadas por endpoint y proceso.
   - Tabla: ID | endpoint | escenario | pregunta | opciones posibles |
     prioridad | fuente.
   - Prioridad: bloqueante, importante o por confirmar.
   - Consecuencia de cada decisión cuando sea relevante.

8. **Cross-Endpoint Consistency**
   - Posibles contradicciones o vacíos entre endpoints relacionados.
   - Secuencias concretas que ilustren sus consecuencias.
   - Preguntas para resolver las diferencias detectadas.

9. **Proposed Acceptance Criteria**
   - Criterios verificables para reglas ya confirmadas.
   - Escenarios pendientes de decisión, marcados como propuestas.
   - Formato sugerido: Dado / Cuando / Entonces.

10. **Coverage and Limitations**
    - Categorías y combinaciones revisadas para cada endpoint.
    - Información faltante y comportamientos no comprobados.
    - Pasos o validaciones que no se pudieron realizar.

## 4) Constraints

### Negocio y alcance

- No implementes endpoints ni modifiques el contrato, salvo que el usuario
  lo solicite expresamente.
- No inventes reglas: diferencia lo explícito, lo inferido y lo desconocido.
- No conviertas una práctica habitual en un requisito sin confirmación.
- No afirmes que existe una contradicción si las fuentes no la sustentan;
  presenta la situación como una posible inconsistencia o pregunta.
- Formula preguntas relacionadas con los endpoints y el contexto recibido.
  Evita agregar preguntas genéricas que no aporten a la funcionalidad.
- Revisa los caminos y categorías aplicables de forma sistemática, pero
  no prometas encontrar todas las posibilidades.

### Contrato y BIAN

- Valida la estructura OpenAPI y revisa sus referencias cuando sea posible.
- Distingue la validez sintáctica o estructural del contrato de la
  coherencia de sus reglas de negocio.
- Trata BIAN como una referencia separada: un contrato válido en OpenAPI
  no es automáticamente conforme a BIAN.
- Compara con una versión y referencia BIAN identificables. Si no están
  disponibles o no puedes consultarlas, indica que la alineación no se
  pudo verificar; no inventes nombres, operaciones ni requisitos.

### Privacidad

- Usa únicamente ejemplos y datos ficticios.
- No incluyas información sensible o secretos en el informe.

## 5) Validation Rules

### Paso 1: Validar el contrato

- Identifica la versión OpenAPI y los endpoints dentro del alcance.
- Revisa métodos, rutas, parámetros, cuerpos, esquemas, respuestas,
  seguridad y referencias aplicables.
- Señala errores o información insuficiente que impidan el análisis.
- Registra si se usó una herramienta de validación y su resultado.

### Paso 2: Identificar reglas y entidades

- Extrae las reglas explícitas de la documentación y el contrato.
- Identifica entidades, relaciones, estados y acciones involucradas.
- Distingue campos obligatorios en el contrato de requisitos de negocio
  que no estén expresados.
- Vincula cada afirmación con su fuente, usando archivo y línea cuando
  estén disponibles.

### Paso 3: Explorar caminos de negocio

Para cada endpoint:

1. Identifica los parámetros, campos, filtros y condiciones que pueden
   influir en el resultado.
2. Identifica las decisiones que no estén definidas por el contrato
   o las reglas disponibles.
3. Construye una matriz de escenarios que considere, cuando aplique:
   - Flujo principal exitoso.
   - Entradas opcionales presentes y ausentes.
   - Valores válidos, inválidos y límites.
   - Recursos existentes, inexistentes o en estados diferentes.
   - Acciones permitidas o no permitidas según el actor.
   - Resultados con datos, sin datos o con información parcial.
   - Operaciones repetidas o dependientes de otras operaciones.
   - Condiciones temporales, como fechas, vencimientos y períodos.
4. Revisa combinaciones relevantes entre condiciones. Agrupa escenarios
   equivalentes y prioriza los que puedan cambiar una decisión de negocio.
5. Clasifica cada camino como definido, ambiguo o no comprobado.
6. Registra las combinaciones que no puedan analizarse y por qué.

### Paso 4: Generar preguntas de negocio

Para cada endpoint, considera las categorías que apliquen:

- **Propósito:** ¿Qué necesidad de negocio resuelve?
- **Actores y acceso:** ¿Quién puede usarlo y sobre qué recursos?
- **Datos:** ¿Qué información debe enviarse, mostrarse u omitirse?
- **Condiciones:** ¿Qué debe cumplirse para realizar la operación?
- **Estados:** ¿Qué estados se permiten y cómo afectan el resultado?
- **Resultados:** ¿Qué debe ocurrir si no hay datos o no se cumple una regla?
- **Relaciones:** ¿Qué entidades relacionadas deben existir o estar activas?
- **Límites:** ¿Hay cantidades, períodos, montos o frecuencias permitidos?
- **Operaciones repetidas:** ¿Qué ocurre si se repite una solicitud?
- **Ciclo de vida:** ¿Cómo impacta la operación en procesos posteriores?

Para consultas de listas, considera además:

- Filtros, ordenamiento, paginación y límites de resultados.
- Períodos de consulta, límites de fechas y zona horaria.
- Comportamiento cuando no se envían filtros.
- Visibilidad de registros pendientes, anulados o históricos.

Para operaciones de creación o modificación, considera además:

- Condiciones previas y transiciones de estado.
- Duplicados y efectos de repetir una operación.
- Reglas para cambios parciales y relaciones entre recursos.

Formula preguntas para cada decisión relevante no definida. Explica
por qué se necesita la respuesta y ofrece opciones cuando ayuden,
sin presentar ninguna como requisito confirmado.

### Paso 5: Comparar endpoints relacionados

- Revisa si un endpoint permite crear o modificar datos que otro requiere
  de forma diferente.
- Analiza si una secuencia válida puede dejar una entidad o proceso en
  un estado cuya gestión no esté definida.
- Identifica diferencias entre términos, estados y condiciones de negocio.
- Si no hay evidencia suficiente, plantea la situación como hipótesis.

### Paso 6: Validar el informe

La salida es válida si:

- Incluye todos los endpoints dentro del alcance.
- Cada endpoint tiene una matriz de caminos relevantes.
- Considera caminos exitosos, alternativos y excepcionales, además de
  secuencias entre endpoints cuando correspondan.
- Cada pregunta está vinculada a un escenario concreto y explica
  la decisión que necesita negocio.
- Identifica las fuentes revisadas y las limitaciones.
- Separa reglas confirmadas de inferencias y preguntas.
- Prioriza las preguntas según su impacto en implementación o negocio.
- Incluye criterios de aceptación cuando exista información suficiente;
  marca los escenarios restantes como pendientes.
- Indica qué revisión BIAN se realizó o por qué no pudo realizarse.
- No afirma que se ejecutaron validaciones que solo fueron propuestas.

## 6) Evidence

Adjunta o referencia, cuando aplique:

- Contrato OpenAPI y documentación de negocio revisados.
- Versión y referencia BIAN utilizada.
- Resultado de validación OpenAPI, si se ejecutó.
- Respuestas y decisiones aprobadas por negocio.
- Criterios de aceptación actualizados después de resolver las preguntas.
- Tag de versión del skill, si el equipo decide publicarlo.