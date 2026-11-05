# Spec Delta

## Purpose

Define el comportamiento observable de la autenticación por credenciales en `POST /auth/login`: qué respuestas produce y la garantía de que los valores recibidos nunca alteran la verificación de credenciales.

## ADDED Requirements

### Requirement: Login con credenciales válidas
El sistema SHALL responder `200` a `POST /auth/login` cuando `username` y `password` coinciden con un usuario registrado, e incluir en el cuerpo un `token` y el objeto `user` con `username`, `displayName` y `role`, además de `expiresIn`.

#### Scenario: Usuario de laboratorio válido
- **WHEN** se envía `POST /auth/login` con `{"username":"student","password":"Workshop123!","client":"angular-workshop"}`
- **THEN** la respuesta es `200`
- **AND** `user.username` es `student`
- **AND** `token` está presente y no está vacío

### Requirement: Rechazo de credenciales inválidas
El sistema SHALL responder `401` sin `token` cuando `username` y `password` no coinciden con un usuario registrado.

#### Scenario: Contraseña incorrecta
- **WHEN** se envía `POST /auth/login` con `username` `student` y una contraseña que no es la registrada
- **THEN** la respuesta es `401`
- **AND** el cuerpo no contiene `token`

#### Scenario: Usuario inexistente
- **WHEN** se envía `POST /auth/login` con un `username` que no existe y cualquier contraseña no vacía
- **THEN** la respuesta es `401`
- **AND** el cuerpo no contiene `token`

### Requirement: Validación de campos obligatorios
El sistema SHALL responder `400` sin `token` cuando el cuerpo no trae `username` o `password`, o cuando alguno de ellos está vacío o solo contiene espacios.

#### Scenario: Usuario en blanco
- **WHEN** se envía `POST /auth/login` con `username` vacío o solo espacios
- **THEN** la respuesta es `400`
- **AND** el cuerpo no contiene `token`

#### Scenario: Contraseña ausente
- **WHEN** se envía `POST /auth/login` con `username` `student` y sin `password`
- **THEN** la respuesta es `400`
- **AND** el cuerpo no contiene `token`

### Requirement: Las credenciales recibidas se tratan solo como datos
El sistema SHALL verificar las credenciales tratando `username` y `password` únicamente como valores a comparar, de modo que ningún carácter de esos campos modifique la lógica de la consulta ni permita autenticarse sin credenciales válidas.

#### Scenario: Intento de inyección en el usuario
- **WHEN** se envía `POST /auth/login` con `username` `' OR '1'='1` y cualquier contraseña no vacía
- **THEN** la respuesta es `401`
- **AND** el cuerpo no contiene `token`

#### Scenario: Intento de inyección en la contraseña
- **WHEN** se envía `POST /auth/login` con `username` `student` y `password` `' OR '1'='1`
- **THEN** la respuesta es `401`
- **AND** el cuerpo no contiene `token`

#### Scenario: Comillas en una credencial no válida
- **WHEN** se envía `POST /auth/login` con un `username` que contiene comillas simples y que no corresponde a ningún usuario registrado
- **THEN** la respuesta es `401`
- **AND** el cuerpo no contiene `token`

#### Scenario: Credenciales válidas siguen funcionando tras la corrección
- **WHEN** se envía `POST /auth/login` con `student` y `Workshop123!`
- **THEN** la respuesta es `200` con `user.username` `student` y `token` presente

### Requirement: Prueba automatizada del intento de inyección
El conjunto de pruebas del componente `auth` SHALL incluir al menos una prueba que ejecute un intento de inyección SQL contra `POST /auth/login` y verifique `401` sin `token`, y SHALL pasar con `mvn test` ejecutado desde `auth/`.

#### Scenario: Suite de auth verde
- **WHEN** se ejecuta `mvn test` desde `auth/`
- **THEN** la prueba de inyección y la prueba de login válido pasan
- **AND** la ejecución termina sin fallos
