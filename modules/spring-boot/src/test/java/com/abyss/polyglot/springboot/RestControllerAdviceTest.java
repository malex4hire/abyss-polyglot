package com.abyss.polyglot.springboot;

import static org.junit.jupiter.api.Assertions.*;

import com.abyss.polyglot.springboot.web.ApiExceptionHandler;
import java.util.List;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.core.MethodParameter;
import org.springframework.validation.BeanPropertyBindingResult;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;

/** Executable proof that the error shape is decided in one advice class that applies to
 *  every controller, rather than per handler. */
@Tag("rest-controller-advice")
class RestControllerAdviceTest {

    @Test
    void errorShapeIsDecidedInOnePlaceForEveryController() throws Exception {
        var binding = new BeanPropertyBindingResult(new Object(), "request");
        binding.addError(new FieldError("request", "status", "must not be null"));
        var parameter = new MethodParameter(
                RestControllerAdviceTest.class.getDeclaredMethod("sample", String.class), 0);

        var response = new ApiExceptionHandler()
                .onValidationFailure(new MethodArgumentNotValidException(parameter, binding));

        assertEquals(422, response.getStatusCode().value());
        assertEquals("validation failed", response.getBody().get("error"));
        assertEquals(1, ((List<?>) response.getBody().get("fields")).size());

        // Calling the method directly asserts the body it builds and nothing about how a
        // thrown exception reaches it — a plain catch block in the controller produces the
        // identical response, so those assertions alone say nothing about the advice.
        // @ExceptionHandler is what makes this reachable from any handler that throws,
        // and it is the mechanism.
        var handler = ApiExceptionHandler.class.getDeclaredMethod(
                "onValidationFailure", MethodArgumentNotValidException.class);
        assertNotNull(handler.getAnnotation(
                        org.springframework.web.bind.annotation.ExceptionHandler.class),
                "without this the method is ordinary code nothing routes to");
        assertNotNull(ApiExceptionHandler.class.getAnnotation(
                        org.springframework.web.bind.annotation.RestControllerAdvice.class),
                "and the class is advice, so the mapping applies to every controller");
    }

    @SuppressWarnings("unused")
    void sample(String status) {
    }
}
