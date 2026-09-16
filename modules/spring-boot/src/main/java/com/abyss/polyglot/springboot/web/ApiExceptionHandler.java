package com.abyss.polyglot.springboot.web;

import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/** Cross-cutting error translation for every controller in the application. */
@RestControllerAdvice
public class ApiExceptionHandler {

    /**
     * One handler, composed into every controller. The advice is discovered at startup
     * and consulted whenever a handler throws, so error shape is decided in one place
     * instead of being repeated in each method — and the controllers stay free of
     * try/catch that has nothing to do with what they are for.
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, Object>> onValidationFailure(MethodArgumentNotValidException e) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("error", "validation failed");
        body.put("fields", e.getBindingResult().getFieldErrors().stream()
                .map(field -> Map.of("field", field.getField(),
                        "message", String.valueOf(field.getDefaultMessage())))
                .toList());
        return ResponseEntity.unprocessableEntity().body(body);
    }
}
