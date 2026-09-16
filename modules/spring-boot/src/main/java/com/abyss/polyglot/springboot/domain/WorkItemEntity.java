package com.abyss.polyglot.springboot.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.Table;
import java.time.Instant;

/**
 * The JPA entity. Mapped by annotation; the schema is managed by Hibernate's ddl-auto
 * rather than by SQL this module writes.
 *
 * Note what is deliberately not shown here. This is a class, not a record: the
 * language-level lessons belong to the java-modern module, and a framework module should
 * not double as one.
 */
@Entity
@Table(name = "work_item", schema = "spring_boot")
public class WorkItemEntity {

    @Id
    private String id;

    private String title;

    @Enumerated(EnumType.STRING)
    private Status status;

    private int priority;

    private String assignee;

    @Column(name = "created_at")
    private Instant createdAt;

    @Column(name = "updated_at")
    private Instant updatedAt;

    private String tags;

    @Column(name = "archived_at")
    private Instant archivedAt;

    protected WorkItemEntity() {
    }

    public WorkItemEntity(String id, String title, Status status, int priority, String assignee,
                          Instant createdAt, Instant updatedAt, String tags, Instant archivedAt) {
        this.id = id;
        this.title = title;
        this.status = status;
        this.priority = priority;
        this.assignee = assignee;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
        this.tags = tags;
        this.archivedAt = archivedAt;
    }

    public String getId() { return id; }
    public String getTitle() { return title; }
    public Status getStatus() { return status; }
    public void setStatus(Status status) { this.status = status; }
    public int getPriority() { return priority; }
    public String getAssignee() { return assignee; }
    public Instant getCreatedAt() { return createdAt; }
    public Instant getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(Instant updatedAt) { this.updatedAt = updatedAt; }
    /** Stored as a delimited column; served as a list, because the shared OpenAPI
     *  contract is one shape across every backend and storage is each module's own
     *  business. */
    @JsonProperty("tags")
    public java.util.List<String> getTagList() {
        return tags == null || tags.isBlank() ? java.util.List.of() : java.util.List.of(tags.split(";"));
    }

    @JsonIgnore
    public String getTags() { return tags; }
    public Instant getArchivedAt() { return archivedAt; }
    public void setArchivedAt(Instant archivedAt) { this.archivedAt = archivedAt; }
}
