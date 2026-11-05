package com.bcp.workshop.auth;

import io.quarkus.test.junit.QuarkusTest;
import io.restassured.response.ValidatableResponse;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.Matchers.greaterThan;
import static org.hamcrest.Matchers.notNullValue;
import static org.hamcrest.Matchers.nullValue;

@QuarkusTest
class AuthResourceTest {
    private static final String LOGIN_PATH = "/auth/login";
    private static final String CLIENT = "angular-workshop";
    private static final String STUDENT_USERNAME = "student";
    private static final String STUDENT_PASSWORD = "Workshop123!";
    private static final int HTTP_OK = 200;
    private static final int HTTP_BAD_REQUEST = 400;
    private static final int HTTP_UNAUTHORIZED = 401;

    @Test
    @DisplayName("Login con credenciales válidas: 200 con token, expiresIn y user completo")
    void logsInWithWorkshopUser() {
        postLogin(Map.of("username", STUDENT_USERNAME, "password", STUDENT_PASSWORD, "client", CLIENT))
                .statusCode(HTTP_OK)
                .body("user.username", is(STUDENT_USERNAME))
                .body("user.displayName", is("Workshop Student"))
                .body("user.role", is("STUDENT"))
                .body("expiresIn", greaterThan(0))
                .body("token", notNullValue());
    }

    @Test
    @DisplayName("Rechazo de credenciales inválidas: contraseña incorrecta para un usuario existente")
    void rejectsWrongPasswordForExistingUser() {
        assertRejectedWithoutToken(postLogin(credentials(STUDENT_USERNAME, "wrong-password")), HTTP_UNAUTHORIZED);
    }

    @Test
    @DisplayName("Rechazo de credenciales inválidas: usuario inexistente")
    void rejectsUnknownUser() {
        assertRejectedWithoutToken(postLogin(credentials("nobody", STUDENT_PASSWORD)), HTTP_UNAUTHORIZED);
    }

    @Test
    @DisplayName("Rechazo de credenciales inválidas: la comparación del usuario distingue mayúsculas")
    void rejectsUsernameWithDifferentCapitalization() {
        assertRejectedWithoutToken(postLogin(credentials("STUDENT", STUDENT_PASSWORD)), HTTP_UNAUTHORIZED);
    }

    @Test
    @DisplayName("Rechazo de credenciales inválidas: la comparación de la contraseña distingue mayúsculas")
    void rejectsPasswordWithDifferentCapitalization() {
        assertRejectedWithoutToken(postLogin(credentials(STUDENT_USERNAME, "workshop123!")), HTTP_UNAUTHORIZED);
    }

    @Test
    @DisplayName("Validación de campos obligatorios: usuario vacío")
    void rejectsEmptyUsername() {
        assertRejectedWithoutToken(postLogin(credentials("", STUDENT_PASSWORD)), HTTP_BAD_REQUEST);
    }

    @Test
    @DisplayName("Validación de campos obligatorios: usuario solo con espacios")
    void rejectsWhitespaceOnlyUsername() {
        assertRejectedWithoutToken(postLogin(credentials("   ", STUDENT_PASSWORD)), HTTP_BAD_REQUEST);
    }

    @Test
    @DisplayName("Validación de campos obligatorios: usuario ausente")
    void rejectsMissingUsername() {
        assertRejectedWithoutToken(
                postLogin(Map.of("password", STUDENT_PASSWORD, "client", CLIENT)), HTTP_BAD_REQUEST);
    }

    @Test
    @DisplayName("Validación de campos obligatorios: contraseña ausente")
    void rejectsMissingPassword() {
        assertRejectedWithoutToken(
                postLogin(Map.of("username", STUDENT_USERNAME, "client", CLIENT)), HTTP_BAD_REQUEST);
    }

    @Test
    @DisplayName("Validación de campos obligatorios: contraseña solo con espacios")
    void rejectsWhitespaceOnlyPassword() {
        assertRejectedWithoutToken(postLogin(credentials(STUDENT_USERNAME, "   ")), HTTP_BAD_REQUEST);
    }

    @Test
    @DisplayName("Rechazo de credenciales inválidas: usuario inexistente con comilla simple")
    void rejectsUnknownUsernameContainingSingleQuote() {
        assertRejectedWithoutToken(postLogin(credentials("o'brien", STUDENT_PASSWORD)), HTTP_UNAUTHORIZED);
    }

    private static Map<String, String> credentials(String username, String password) {
        return Map.of("username", username, "password", password, "client", CLIENT);
    }

    private static ValidatableResponse postLogin(Map<String, String> body) {
        return given()
                .contentType("application/json")
                .body(body)
                .when().post(LOGIN_PATH)
                .then();
    }

    private static void assertRejectedWithoutToken(ValidatableResponse response, int expectedStatus) {
        response.statusCode(expectedStatus).body("token", nullValue());
    }
}
