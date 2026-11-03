ROL
Actúa como analista de negocio y senior software engineer especializado
en identificar contradicciones, ambigüedades y vacíos en reglas de negocio.

ÁMBITO
El workspace ai-labs está abierto en su raíz.
Lee código únicamente en api/. Todas las rutas parten de la raíz.

Lee README.md, RETO.md y los documentos generales relevantes de docs/.
Consulta la especificación OpenAPI si existe dentro del alcance permitido.

Este pedido es de solo lectura: no escribas ni modifiques archivos.
No leas ni modifiques código de auth/ ni web/.
Git se ejecuta desde la raíz; las pruebas locales usan cwd api/.
Usa IDs H-API-NN y componente api.

OBJETIVO
Identifica posibles contradicciones, ambigüedades o vacíos en las
reglas de negocio aplicadas por los endpoints, especialmente cuando
varios endpoints operan sobre las mismas entidades o procesos.

No centres la revisión en errores técnicos. Analiza si las operaciones
permitidas por un endpoint son coherentes con las condiciones y
restricciones establecidas por otros endpoints y por la documentación.

ANÁLISIS
1. Identifica todas las entidades de negocio, sus relaciones y los
   endpoints que permiten crearlas, consultarlas, modificarlas,
   eliminarlas o cambiar su estado.

2. Extrae las reglas de negocio presentes en la documentación y en el
   código. Para cada regla, indica su fuente y distingue entre:
   - Regla documentada.
   - Regla implementada en código.
   - Regla inferida que necesita confirmación.

3. Compara las reglas entre endpoints relacionados. Busca, por ejemplo:
   - Un endpoint permite crear A sin B, pero otro proceso presupone
     que toda entidad A debe estar asociada a B.
   - Un endpoint permite eliminar o desactivar B mientras otro requiere
     que B exista o esté activo para que A siga siendo válido.
   - Una operación permite un estado que otro endpoint considera inválido.
   - Un recurso puede crearse con valores que luego no puede actualizar
     o que impiden completar su proceso.
   - Un endpoint permite repetir una operación que otro trata como única.
   - Dos endpoints aplican condiciones diferentes para la misma acción.
   - Una regla documentada exige una condición que ningún endpoint
     comprueba, o el código exige una condición no documentada.

4. Revisa los ciclos de vida completos de las entidades y los procesos:
   creación, asociaciones, cambios de estado, actualización y eliminación.
   Identifica secuencias de acciones que puedan dejar una entidad o
   proceso en una situación incoherente.

5. Busca evidencia en las pruebas existentes e identifica los escenarios
   de negocio que no estén cubiertos.

RESTRICCIONES
- No edites código ni ejecutes pruebas contra servicios remotos.
- Usa únicamente código y datos ficticios locales.
- No cambies contratos ni leas otros componentes.
- Si una regla depende de auth/, web/ o una integración externa,
  identifica la dependencia y marca su comportamiento como no comprobado.
- No inventes requisitos ni afirmes que una regla falta solo porque sería
  deseable. Si no está clara la intención del negocio, plantea una pregunta.
- Distingue contradicciones demostrables de posibles inconsistencias
  que requieren confirmación.
- Si una prueba local pudiera escribir archivos o modificar datos,
  no la ejecutes: propón el escenario y explica el riesgo.
- No asegures que encontraste todas las inconsistencias posibles;
  indica los límites de la revisión.

CRITERIOS DE ACEPTACIÓN
Para cada hallazgo:

- Identifica las entidades, procesos y endpoints involucrados.
- Cita las reglas y la evidencia correspondiente con archivo:línea.
- Describe una secuencia concreta de acciones con datos ficticios.
- Explica qué resultado permite o exige cada regla y por qué podrían
  entrar en conflicto.
- Clasifica el hallazgo como contradicción confirmada, posible
  inconsistencia, ambigüedad o comportamiento no comprobado.
- Propone una pregunta para el responsable de negocio cuando no haya
  suficiente evidencia para decidir cuál debe ser el comportamiento.
- Propone una prueba de negocio con resultado esperado, si la regla
  está suficientemente definida. No afirmes que pasó si no la ejecutaste.

FORMATO DE RESPUESTA
1. Mapa de entidades y procesos:
   entidad | relaciones | endpoints involucrados | reglas relevantes

2. Tabla de hallazgos:
   ID | entidad o proceso | endpoints | reglas en conflicto |
   evidencia archivo:línea | escenario de negocio | consecuencia |
   clasificación | prueba propuesta o pregunta de negocio

3. Reglas ambiguas y preguntas abiertas para negocio.

4. Alcance y limitaciones de la revisión.

5. Comandos ejecutados y resultados; comandos propuestos no ejecutados.