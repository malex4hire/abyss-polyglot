-- Schema per backend module (Additional Constraints). Created before any module starts,
-- because Hibernate's default_schema does not create the schema it is pointed at and
-- Spring's DDL runs after the connection is already scoped to it.
CREATE SCHEMA IF NOT EXISTS spring_traditional;
CREATE SCHEMA IF NOT EXISTS spring_boot;
