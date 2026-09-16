package com.abyss.polyglot.springtraditional.web;

import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * Error translation for the traditional stack.
 *
 * Declared here by hand and registered by the component scan. Boot ships a default error
 * shape you override; here there is no default, so an unhandled exception reaches the
 * container and becomes a 500 page rather than the client error the contract promises.
 */
@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<Map<String, String>> onBadValue(IllegalArgumentException e) {
        return ResponseEntity.badRequest()
                .body(Map.of("error", "bad request", "detail", String.valueOf(e.getMessage())));
    }
}
