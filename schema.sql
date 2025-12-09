CREATE DATABASE IF NOT EXISTS curriculum_tracker;
USE curriculum_tracker;

-- Degree: degree programs (BA, BS, MS, Ph.D., Cert)
CREATE TABLE IF NOT EXISTS Degree (
    name VARCHAR(100) NOT NULL,
    level VARCHAR(50) NOT NULL,
    description TEXT,
    PRIMARY KEY (name, level),
    CONSTRAINT ck_degree_level CHECK (level IN ('BA','BS','MS','Ph.D.','Cert'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Course: catalog courses; reusable by multiple degrees
CREATE TABLE IF NOT EXISTS Course (
    course_no VARCHAR(20) NOT NULL,
    title VARCHAR(120) NOT NULL,
    description TEXT,
    PRIMARY KEY (course_no),
    CONSTRAINT uq_course_title UNIQUE (title),
    CONSTRAINT ck_course_number CHECK (course_no REGEXP '^[A-Za-z]{2,4}[0-9]{4}$')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Instructor: faculty directory keyed only by instructor_id
CREATE TABLE IF NOT EXISTS Instructor (
    instructor_id VARCHAR(20) NOT NULL,
    name VARCHAR(120) NOT NULL,
    PRIMARY KEY (instructor_id),
    CONSTRAINT uq_instructor_name UNIQUE (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Semester: allowed year/term combinations for scheduling sections
CREATE TABLE IF NOT EXISTS Semester (
    year INT NOT NULL,
    term VARCHAR(10) NOT NULL,
    PRIMARY KEY (year, term),
    CONSTRAINT ck_semester_term CHECK (term IN ('Spring','Summer','Fall'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Section: concrete offerings with instructor and enrollment info
CREATE TABLE IF NOT EXISTS Section (
    course_no VARCHAR(20) NOT NULL,
    year INT NOT NULL,
    term VARCHAR(10) NOT NULL,
    section_no CHAR(3) NOT NULL,
    instructor_id VARCHAR(20) NOT NULL,
    enrolled_count INT NOT NULL,
    PRIMARY KEY (course_no, year, term, section_no),
    CONSTRAINT fk_section_course FOREIGN KEY (course_no) REFERENCES Course(course_no),
    CONSTRAINT fk_section_semester FOREIGN KEY (year, term) REFERENCES Semester(year, term),
    CONSTRAINT fk_section_instructor FOREIGN KEY (instructor_id) REFERENCES Instructor(instructor_id),
    CONSTRAINT ck_section_enrollment CHECK (enrolled_count >= 0),
    CONSTRAINT ck_section_number CHECK (section_no REGEXP '^[0-9]{3}$')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Objective: learning objectives with unique short codes and titles
CREATE TABLE IF NOT EXISTS Objective (
    code VARCHAR(20) NOT NULL,
    title VARCHAR(120) NOT NULL,
    description TEXT,
    PRIMARY KEY (code),
    CONSTRAINT uq_objective_title UNIQUE (title),
    CONSTRAINT ck_objective_code CHECK (code REGEXP '^OBJ[0-9]{3}$')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- DegreeCourse: relationship between Degree and Course, with core flag
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

-- DegreeCourseObjective: degree-specific objective assignments per course
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

-- Evaluation: per-section, per-objective assessment data
CREATE TABLE IF NOT EXISTS Evaluation (
    course_no VARCHAR(20) NOT NULL,
    year INT NOT NULL,
    term VARCHAR(10) NOT NULL,
    section_no CHAR(3) NOT NULL,
    name VARCHAR(100) NOT NULL,
    level VARCHAR(50) NOT NULL,
    objective_code VARCHAR(20) NOT NULL,
    method_label VARCHAR(40) NOT NULL,
    a_count INT NOT NULL DEFAULT 0,
    b_count INT NOT NULL DEFAULT 0,
    c_count INT NOT NULL DEFAULT 0,
    f_count INT NOT NULL DEFAULT 0,
    improvement_text VARCHAR(2000) NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (course_no, year, term, section_no, name, level, objective_code, method_label),
    CONSTRAINT fk_eval_section FOREIGN KEY (course_no, year, term, section_no)
        REFERENCES Section(course_no, year, term, section_no) ON DELETE CASCADE,
    CONSTRAINT fk_eval_dco FOREIGN KEY (name, level, course_no, objective_code)
        REFERENCES DegreeCourseObjective(name, level, course_no, objective_code) ON DELETE CASCADE,
    CONSTRAINT ck_eval_counts_nonneg CHECK (
        a_count >= 0 AND
        b_count >= 0 AND
        c_count >= 0 AND
        f_count >= 0
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
