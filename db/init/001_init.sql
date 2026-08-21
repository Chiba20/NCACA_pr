-- ============================================================
-- NCACA Database Initialization
-- File: db/init/001_init.sql
--
-- Purpose:
--   1. Create the PostgreSQL schemas.
--   2. Create MASTER and TXN tables from the supplied schema.
--   3. Master/reference DATA is populated separately by seed_master.py
--      from seeds/master/*.csv or *.json.
--
-- Notes:
--   - analysis/reporting schemas are created here as placeholders because
--     they are part of the backend architecture, but their table definitions
--     were not present in the supplied Master/Transaction schema document.
--   - Allowed-value hints from the source document are kept as comments
--     rather than hard CHECK constraints unless the source explicitly
--     specified a relational constraint.
-- ============================================================

BEGIN;

-- ============================================================
-- 1. SCHEMAS
-- ============================================================

CREATE SCHEMA IF NOT EXISTS master;
CREATE SCHEMA IF NOT EXISTS txn;
CREATE SCHEMA IF NOT EXISTS analysis;
CREATE SCHEMA IF NOT EXISTS reporting;


-- ============================================================
-- 2. MASTER SCHEMA
-- ============================================================

-- ------------------------------------------------------------
-- Geography
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS master.island (
    island_id      BIGSERIAL PRIMARY KEY,
    island_name    VARCHAR UNIQUE
    -- expected examples: Unguja, Pemba
);

CREATE TABLE IF NOT EXISTS master.district (
    district_id    BIGSERIAL PRIMARY KEY,
    island_id      BIGINT REFERENCES master.island(island_id),
    district_name  VARCHAR
);


-- ------------------------------------------------------------
-- Schools
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS master.school (
    school_id               BIGSERIAL PRIMARY KEY,
    zec_code                VARCHAR UNIQUE,
    district_id             BIGINT REFERENCES master.district(district_id),
    school_name             VARCHAR,
    locality_type           VARCHAR,   -- URBAN | RURAL
    address_line            VARCHAR,
    management_type         VARCHAR,   -- GOVT | PRIVATE | COMMUNITY
    medium_of_instruction   VARCHAR,   -- Swahili | English
    school_type             VARCHAR    -- Primary | Secondary
);


-- ------------------------------------------------------------
-- Core Lookups
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS master.grade (
    grade_id          BIGSERIAL PRIMARY KEY,
    grade_code        VARCHAR UNIQUE,  -- Std3 | Std7 | Form2 | Form4
    grade_label       VARCHAR,
    education_stage   VARCHAR
);

CREATE TABLE IF NOT EXISTS master.subject (
    subject_id        BIGSERIAL PRIMARY KEY,
    subject_name      VARCHAR UNIQUE
    -- examples: Kiswahili, English, Mathematics, Science, Social Studies
);


-- ------------------------------------------------------------
-- Curriculum Framework
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS master.curricular_goal (
    curricular_goal_id   BIGSERIAL PRIMARY KEY,
    subject_id           BIGINT REFERENCES master.subject(subject_id),
    grade_id             BIGINT REFERENCES master.grade(grade_id),
    goal_code            VARCHAR,
    goal_description     TEXT
);

CREATE TABLE IF NOT EXISTS master.competency (
    competency_id           BIGSERIAL PRIMARY KEY,
    curricular_goal_id      BIGINT REFERENCES master.curricular_goal(curricular_goal_id),
    competency_code         VARCHAR UNIQUE,
    competency_description  TEXT
);


-- ------------------------------------------------------------
-- Key Area Catalogue
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS master.key_area_catalogue (
    record_code              VARCHAR PRIMARY KEY,
    grade_id                 BIGINT REFERENCES master.grade(grade_id),
    subject_id               BIGINT NULL REFERENCES master.subject(subject_id),
    area_number              SMALLINT,
    intervention_area        TEXT,
    subject_domain           VARCHAR,
    indicator_code           VARCHAR NULL,
    potential_key_area       TEXT,
    source_type              VARCHAR,   -- LEARNING_ACHIEVEMENT | QUESTIONNAIRE
    respondent               VARCHAR,   -- STUDENT_ASSESSMENT | STUDENT | TEACHER | SCHOOL
    desired_direction        VARCHAR,   -- HIGHER_IS_BETTER | LOWER_IS_BETTER
    default_benchmark_pct    NUMERIC(5,2) NULL,
    suggested_intervention   TEXT NULL,

    CONSTRAINT uq_key_area_catalogue_grade_area
        UNIQUE (grade_id, area_number)
);


-- ------------------------------------------------------------
-- Question Bank
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS master.item_block (
    block_id       BIGSERIAL PRIMARY KEY,
    block_code     VARCHAR,
    subject_id     BIGINT REFERENCES master.subject(subject_id),
    grade_id       BIGINT REFERENCES master.grade(grade_id),
    block_number   SMALLINT
);

CREATE TABLE IF NOT EXISTS master.booklet (
    booklet_id     BIGSERIAL PRIMARY KEY,
    booklet_code   VARCHAR,
    grade_id       BIGINT REFERENCES master.grade(grade_id),
    block_ids      SMALLINT[]
);

CREATE TABLE IF NOT EXISTS master.booklet_block (
    booklet_block_id   BIGSERIAL PRIMARY KEY,
    booklet_id         BIGINT REFERENCES master.booklet(booklet_id),
    block_id           BIGINT REFERENCES master.item_block(block_id)
);

CREATE TABLE IF NOT EXISTS master.question (
    question_id       BIGSERIAL PRIMARY KEY,
    block_id          BIGINT REFERENCES master.item_block(block_id),
    competency_id     BIGINT REFERENCES master.competency(competency_id),
    question_number   SMALLINT,
    question_text     TEXT,
    max_marks         NUMERIC,
    difficulty_level  VARCHAR,
    item_type         VARCHAR,   -- e.g. mcq
    is_anchor         BOOLEAN,
    status            VARCHAR    -- active | retired | draft
);

CREATE TABLE IF NOT EXISTS master.answer_option (
    answer_option_id   BIGSERIAL PRIMARY KEY,
    question_id        BIGINT REFERENCES master.question(question_id),
    option_code        VARCHAR,   -- A | B | C | D
    option_text        TEXT,
    is_correct         SMALLINT
);


-- ------------------------------------------------------------
-- Contextual Questionnaire
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS master.questionnaire (
    questionnaire_id     BIGSERIAL PRIMARY KEY,
    questionnaire_code   VARCHAR,   -- PQ | TQ | SQ
    questionnaire_name   VARCHAR,
    target_group         VARCHAR    -- student | teacher | school
);

CREATE TABLE IF NOT EXISTS master.questionnaire_item (
    questionnaire_item_id   BIGSERIAL PRIMARY KEY,
    questionnaire_id        BIGINT REFERENCES master.questionnaire(questionnaire_id),
    item_code               VARCHAR,
    item_text               TEXT,
    alert_direction         VARCHAR,   -- above | below
    group_name              VARCHAR
);


-- ============================================================
-- 3. TRANSACTION SCHEMA
-- ============================================================

-- ------------------------------------------------------------
-- Cycle Anchor
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS txn.survey_cycle (
    cycle_id      BIGSERIAL PRIMARY KEY,
    survey_name   VARCHAR,
    cycle_year    SMALLINT,
    status        VARCHAR    -- planned | completed | archived
);


-- ------------------------------------------------------------
-- Assessment Definition & Framework Mapping
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS txn.assessment (
    assessment_id      BIGSERIAL PRIMARY KEY,
    cycle_id           BIGINT REFERENCES txn.survey_cycle(cycle_id),
    grade_id           BIGINT REFERENCES master.grade(grade_id),
    duration_minutes   SMALLINT,
    total_items        SMALLINT,
    max_score          NUMERIC
);

CREATE TABLE IF NOT EXISTS txn.assessment_booklet (
    assessment_booklet_id   BIGSERIAL PRIMARY KEY,
    assessment_id           BIGINT REFERENCES txn.assessment(assessment_id),
    booklet_id              BIGINT REFERENCES master.booklet(booklet_id)
);


-- ------------------------------------------------------------
-- Participants
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS txn.student (
    student_id                 BIGSERIAL PRIMARY KEY,
    cycle_id                   BIGINT REFERENCES txn.survey_cycle(cycle_id),
    school_id                  BIGINT REFERENCES master.school(school_id),
    grade_id                   BIGINT REFERENCES master.grade(grade_id),
    student_code               VARCHAR,
    gender                     VARCHAR,   -- M | F
    age                        SMALLINT,
    language_of_instruction    VARCHAR,
    language_of_assessment     VARCHAR,
    optional_subject           VARCHAR
);

CREATE TABLE IF NOT EXISTS txn.student_disability (
    student_id        BIGINT REFERENCES txn.student(student_id),
    disability_type   VARCHAR,

    PRIMARY KEY (student_id, disability_type)
);

CREATE TABLE IF NOT EXISTS txn.teacher (
    teacher_id   BIGSERIAL PRIMARY KEY,
    cycle_id     BIGINT REFERENCES txn.survey_cycle(cycle_id),
    school_id    BIGINT REFERENCES master.school(school_id),
    grade_id     BIGINT REFERENCES master.grade(grade_id)
);

CREATE TABLE IF NOT EXISTS txn.student_booklet (
    student_booklet_id   BIGSERIAL PRIMARY KEY,
    student_id           BIGINT REFERENCES txn.student(student_id),
    booklet_id           BIGINT REFERENCES master.booklet(booklet_id)
);


-- ------------------------------------------------------------
-- Student Response Staging
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS txn.stg_student_response (
    stg_response_id          BIGSERIAL PRIMARY KEY,
    cycle_id                 BIGINT REFERENCES txn.survey_cycle(cycle_id),
    external_student_code    VARCHAR,
    school_code              VARCHAR,
    booklet_code             VARCHAR,
    question_number          SMALLINT,
    selected_answer          VARCHAR,
    raw_response_text        TEXT,
    response_position        SMALLINT,
    validation_status        VARCHAR,   -- pending | valid | invalid
    validation_error         TEXT,

    CONSTRAINT uq_stg_student_response
        UNIQUE (
            cycle_id,
            school_code,
            external_student_code,
            question_number
        )
);


-- ------------------------------------------------------------
-- Validated Student Responses
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS txn.student_response (
    response_id       BIGSERIAL PRIMARY KEY,
    student_id        BIGINT REFERENCES txn.student(student_id),
    question_id       BIGINT REFERENCES master.question(question_id),
    selected_answer   VARCHAR,
    obtained_marks    NUMERIC,
    response_code     SMALLINT,   -- 7=invalid, 8=omitted, 9=not-reached, NULL=ordinary
    response_status   VARCHAR,    -- valid | invalid | omitted | not_reached
    is_correct        SMALLINT    -- 0/1, NULL if not-reached
);


-- ------------------------------------------------------------
-- Questionnaire Responses
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS txn.pq_responses (
    pq_response_id         BIGSERIAL PRIMARY KEY,
    cycle_id               BIGINT REFERENCES txn.survey_cycle(cycle_id),
    student_id             BIGINT NULL REFERENCES txn.student(student_id),
    questionnaire_item_id  BIGINT REFERENCES master.questionnaire_item(questionnaire_item_id),
    selected_response      TEXT,

    CONSTRAINT uq_pq_responses
        UNIQUE (cycle_id, student_id, questionnaire_item_id)
);

CREATE TABLE IF NOT EXISTS txn.sq_responses (
    sq_response_id         BIGSERIAL PRIMARY KEY,
    cycle_id               BIGINT REFERENCES txn.survey_cycle(cycle_id),
    school_id              BIGINT NOT NULL REFERENCES master.school(school_id),
    questionnaire_item_id  BIGINT REFERENCES master.questionnaire_item(questionnaire_item_id),
    selected_response      TEXT,

    CONSTRAINT uq_sq_responses
        UNIQUE (cycle_id, school_id, questionnaire_item_id)
);

CREATE TABLE IF NOT EXISTS txn.tq_responses (
    tq_response_id         BIGSERIAL PRIMARY KEY,
    cycle_id               BIGINT REFERENCES txn.survey_cycle(cycle_id),
    teacher_id             BIGINT NOT NULL REFERENCES txn.teacher(teacher_id),
    questionnaire_item_id  BIGINT REFERENCES master.questionnaire_item(questionnaire_item_id),
    selected_response      TEXT,

    CONSTRAINT uq_tq_responses
        UNIQUE (cycle_id, teacher_id, questionnaire_item_id)
);


COMMIT;
