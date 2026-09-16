package com.abyss.polyglot.springboot.web;

import com.abyss.polyglot.springboot.domain.Status;
import jakarta.validation.constraints.NotNull;

/** The transition payload, validated before the handler sees it. */
public record TransitionRequest(@NotNull Status status) {
}
