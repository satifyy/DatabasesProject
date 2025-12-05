CREATE DATABASE IF NOT EXISTS curriculum_tracker;
USE curriculum_tracker;

CREATE TABLE IF NOT EXISTS Degree (
    name VARCHAR(100) NOT NULL,
    level VARCHAR(50) NOT NULL,
    description TEXT,
    PRIMARY KEY (name, level),
    CONSTRAINT ck_degree_level CHECK (level IN ('Associate','Bachelors','Masters','Doctorate','Certificate'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS Course (
    course_no VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    PRIMARY KEY (course_no),
    UNIQUE KEY uq_course_title (title)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS Instructor (
    instructor_id VARCHAR(20) NOT NULL,
    name VARCHAR(120) NOT NULL,
    PRIMARY KEY (instructor_id),
    UNIQUE KEY uq_instructor_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS Semester (
    year INT NOT NULL,
    term VARCHAR(10) NOT NULL,
    PRIMARY KEY (year, term),
    CONSTRAINT ck_semester_term CHECK (term IN ('Spring','Summer','Fall'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS Section (
    course_no VARCHAR(20) NOT NULL,
    year INT NOT NULL,
    term VARCHAR(10) NOT NULL,
    section_no VARCHAR(10) NOT NULL,
    instructor_id VARCHAR(20) NOT NULL,
    enrolled_count INT NOT NULL,
    PRIMARY KEY (course_no, year, term, section_no),
    CONSTRAINT fk_section_course FOREIGN KEY (course_no) REFERENCES Course(course_no),
    CONSTRAINT fk_section_semester FOREIGN KEY (year, term) REFERENCES Semester(year, term),
    CONSTRAINT fk_section_instructor FOREIGN KEY (instructor_id) REFERENCES Instructor(instructor_id),
    CONSTRAINT ck_section_enrollment CHECK (enrolled_count >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS Objective (
    code VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    PRIMARY KEY (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS DegreeCourse (
    name VARCHAR(100) NOT NULL,
    level VARCHAR(50) NOT NULL,
    course_no VARCHAR(20) NOT NULL,
    is_core BOOLEAN NOT NULL DEFAULT 0,
    PRIMARY KEY (name, level, course_no),
    CONSTRAINT fk_degreecourse_degree FOREIGN KEY (name, level) REFERENCES Degree(name, level) ON DELETE CASCADE,
    CONSTRAINT fk_degreecourse_course FOREIGN KEY (course_no) REFERENCES Course(course_no) ON DELETE CASCADE,
    CONSTRAINT ck_degreecourse_is_core CHECK (is_core IN (0,1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS DegreeCourseObjective (
    name VARCHAR(100) NOT NULL,
    level VARCHAR(50) NOT NULL,
    course_no VARCHAR(20) NOT NULL,
    objective_code VARCHAR(20) NOT NULL,
    PRIMARY KEY (name, level, course_no, objective_code),
    CONSTRAINT fk_dco_degreecourse FOREIGN KEY (name, level, course_no)
        REFERENCES DegreeCourse(name, level, course_no) ON DELETE CASCADE,
    CONSTRAINT fk_dco_objective FOREIGN KEY (objective_code)
        REFERENCES Objective(code) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS Evaluation (
    course_no VARCHAR(20) NOT NULL,
    year INT NOT NULL,
    term VARCHAR(10) NOT NULL,
    section_no VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    level VARCHAR(50) NOT NULL,
    objective_code VARCHAR(20) NOT NULL,
    method_label VARCHAR(120) NULL,
    a_count INT NULL,
    b_count INT NULL,
    c_count INT NULL,
    f_count INT NULL,
    improvement_text TEXT NULL,
    PRIMARY KEY (course_no, year, term, section_no, name, level, objective_code),
    CONSTRAINT fk_eval_section FOREIGN KEY (course_no, year, term, section_no)
        REFERENCES Section(course_no, year, term, section_no) ON DELETE CASCADE,
    CONSTRAINT fk_eval_dco FOREIGN KEY (name, level, course_no, objective_code)
        REFERENCES DegreeCourseObjective(name, level, course_no, objective_code) ON DELETE CASCADE,
    CONSTRAINT ck_eval_counts_nonneg CHECK (
        (a_count IS NULL OR a_count >= 0) AND
        (b_count IS NULL OR b_count >= 0) AND
        (c_count IS NULL OR c_count >= 0) AND
        (f_count IS NULL OR f_count >= 0)
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
