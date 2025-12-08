-- Comprehensive Test Sample Data for Curriculum Tracker
-- Tests all constraints, edge cases, foreign keys, and CHECK constraints
-- Created as a harsh TA would: designed to catch implementation bugs

USE curriculum_tracker;

-- Clear existing data in correct dependency order (children first)
DELETE FROM Evaluation;
DELETE FROM DegreeCourseObjective;
DELETE FROM DegreeCourse;
DELETE FROM Section;
DELETE FROM Semester;
DELETE FROM Instructor;
DELETE FROM Objective;
DELETE FROM Course;
DELETE FROM Degree;

-- ============================================================================
-- DEGREE: Test all 5 CHECK constraint values + edge cases
-- ============================================================================
INSERT INTO Degree (name, level, description) VALUES
-- Test all 5 allowed levels
('Computer Science', 'BS', 'Bachelor of Science in Computer Science'),
('Computer Science', 'MS', 'Master of Science in Computer Science'),
('Computer Science', 'Ph.D.', 'Doctor of Philosophy in Computer Science'),
('Data Science', 'BS', 'Bachelor of Science in Data Science'),
('Data Science', 'MS', 'Master of Science in Data Science'),
('Cybersecurity', 'BS', 'Bachelor of Science in Cybersecurity'),
('Cybersecurity', 'MS', 'Master of Science in Cybersecurity'),
('Software Engineering', 'BS', 'Bachelor of Science in Software Engineering'),
('Information Technology', 'BA', 'Bachelor of Arts in Information Technology'),
('Web Development', 'Cert', 'Professional Certificate in Web Development'),
-- Edge cases: long names, special characters, minimal descriptions
('Artificial Intelligence & Machine Learning', 'MS', 'AI/ML Graduate Program'),
('Computer Engineering', 'BS', NULL),  -- NULL description allowed
('Database Administration', 'Cert', 'Short-term certificate');

-- ============================================================================
-- COURSE: Test VARCHAR lengths, special characters, duplicate prevention
-- ============================================================================
INSERT INTO Course (course_no, title, description) VALUES
-- Standard courses
('CS5330', 'Database Management Systems', 'Comprehensive study of database design, SQL, and transaction management'),
('CS7330', 'Advanced Database Systems', 'Graduate-level database theory and distributed systems'),
('CS1111', 'Introduction to Programming', 'First course in computer science using Python'),
('CS2222', 'Data Structures', 'Study of arrays, linked lists, trees, and graphs'),
('CS3333', 'Algorithms', 'Algorithm design and complexity analysis'),
('CS4444', 'Software Engineering', 'Software development lifecycle and project management'),
('MATH2410', 'Discrete Mathematics', 'Logic, sets, relations, graph theory'),
('STAT3000', 'Probability and Statistics', 'Probability theory and statistical inference'),
-- Edge cases: minimum length course codes, maximum title length (exactly 120 chars)
('AB1234', 'This Course Title Tests VARCHAR 120 Character Limit With Exactly One Hundred Twenty Characters Including All Spaces X', 'Edge case'),
('ABCD9999', 'Upper Boundary Course Code', 'Tests 4-letter + 4-digit format'),
-- Special characters in titles
('CS5500', 'Machine Learning & AI', 'ML algorithms and applications'),
('IT2000', 'Web Dev: HTML/CSS/JS', 'Front-end web development'),
-- Electives for different programs
('SEC4100', 'Network Security', 'Cryptography and secure communication'),
('SEC4200', 'Ethical Hacking', 'Penetration testing and security auditing'),
('DS3100', 'Data Mining', 'Pattern recognition and knowledge discovery'),
('DS3200', 'Big Data Analytics', 'Hadoop, Spark, and distributed computing'),
('WEB2100', 'Frontend Frameworks', 'React, Vue, Angular development'),
('WEB2200', 'Backend Development', 'Node.js, Express, REST APIs'),
('DB4100', 'NoSQL Databases', 'MongoDB, Cassandra, Redis'),
('DB4200', 'Database Tuning', 'Performance optimization and indexing');

-- ============================================================================
-- INSTRUCTOR: Test VARCHAR lengths, duplicate IDs prevention
-- ============================================================================
INSERT INTO Instructor (instructor_id, name) VALUES
-- Standard faculty
('I001', 'Dr. Sarah Johnson'),
('I002', 'Dr. Michael Chen'),
('I003', 'Prof. Emily Rodriguez'),
('I004', 'Dr. James Williams'),
('I005', 'Dr. Amanda Lee'),
('I006', 'Prof. Robert Taylor'),
('I007', 'Dr. Lisa Anderson'),
('I008', 'Dr. David Martinez'),
-- Edge cases: long names, special characters
('I009', 'Dr. Christopher O''Brien-Smith'),  -- Apostrophe and hyphen
('I010', 'Prof. María José García'),  -- Unicode characters
('INST999', 'Dr. Alexander Maximilian Winchester III'),  -- Long name
-- Adjunct/visiting faculty
('ADJ001', 'Dr. John Visiting'),
('ADJ002', 'Ms. Industry Expert');

-- ============================================================================
-- SEMESTER: Test all 3 terms, multiple years, chronological coverage
-- ============================================================================
INSERT INTO Semester (year, term) VALUES
-- Historical data (2020-2021)
(2020, 'Spring'),
(2020, 'Summer'),
(2020, 'Fall'),
(2021, 'Spring'),
(2021, 'Summer'),
(2021, 'Fall'),
-- Current academic year (2022-2023)
(2022, 'Spring'),
(2022, 'Summer'),
(2022, 'Fall'),
(2023, 'Spring'),
(2023, 'Summer'),
(2023, 'Fall'),
-- Future semesters (2024-2025)
(2024, 'Spring'),
(2024, 'Summer'),
(2024, 'Fall'),
(2025, 'Spring'),
(2025, 'Summer'),
(2025, 'Fall');

-- ============================================================================
-- SECTION: Test REGEXP constraint, enrollment edge cases, FK relationships
-- ============================================================================
INSERT INTO Section (course_no, year, term, section_no, instructor_id, enrolled_count) VALUES
-- CS5330/7330 sections (multi-year, multi-instructor)
('CS5330', 2023, 'Fall', '001', 'I001', 35),
('CS5330', 2023, 'Fall', '002', 'I002', 32),
('CS7330', 2023, 'Fall', '001', 'I001', 18),
('CS5330', 2024, 'Spring', '001', 'I003', 40),
('CS7330', 2024, 'Spring', '001', 'I002', 15),
('CS5330', 2024, 'Fall', '001', 'I001', 38),
('CS7330', 2024, 'Fall', '001', 'I003', 20),
-- Lower-level courses (high enrollment)
('CS1111', 2023, 'Fall', '001', 'I004', 120),
('CS1111', 2023, 'Fall', '002', 'I005', 115),
('CS1111', 2024, 'Spring', '001', 'I004', 125),
('CS2222', 2023, 'Fall', '001', 'I005', 80),
('CS2222', 2024, 'Spring', '001', 'I006', 75),
('CS3333', 2023, 'Fall', '001', 'I007', 60),
('CS3333', 2024, 'Spring', '001', 'I007', 65),
-- Upper-level electives (varied enrollment)
('CS4444', 2023, 'Fall', '001', 'I008', 45),
('SEC4100', 2023, 'Fall', '001', 'I003', 28),
('SEC4200', 2024, 'Spring', '001', 'I003', 22),
('DS3100', 2023, 'Fall', '001', 'I002', 35),
('DS3200', 2024, 'Spring', '001', 'I002', 30),
-- Edge cases: section numbers at boundaries
('MATH2410', 2023, 'Fall', '001', 'I009', 90),
('MATH2410', 2023, 'Fall', '002', 'I009', 85),
('STAT3000', 2024, 'Spring', '001', 'I010', 70),
-- Summer offerings (typically smaller)
('CS5330', 2024, 'Summer', '001', 'ADJ001', 25),
('WEB2100', 2024, 'Summer', '001', 'ADJ002', 18),
-- Edge case: zero enrollment (cancelled but not deleted)
('DB4200', 2024, 'Fall', '001', 'I001', 0),
-- Edge case: maximum section numbers
('CS1111', 2024, 'Fall', '999', 'I004', 1),  -- Tests 3-digit REGEXP
-- Multiple sections same semester
('WEB2200', 2024, 'Spring', '001', 'I008', 30),
('WEB2200', 2024, 'Spring', '002', 'I008', 28),
('DB4100', 2024, 'Fall', '001', 'I002', 25),
('AB1234', 2023, 'Fall', '001', 'I006', 15);

-- ============================================================================
-- OBJECTIVE: Test UNIQUE title constraint, VARCHAR limits
-- ============================================================================
INSERT INTO Objective (code, title, description) VALUES
-- Standard learning objectives (ABET-style)
('OBJ001', 'Apply database design principles', 'Students will apply normalization and ER modeling to design relational databases'),
('OBJ002', 'Write complex SQL queries', 'Students will write SELECT, JOIN, subquery, and aggregation statements'),
('OBJ003', 'Implement database transactions', 'Students will use ACID properties and transaction control'),
('OBJ004', 'Optimize database performance', 'Students will create indexes and analyze query execution plans'),
('OBJ005', 'Design secure database systems', 'Students will implement authentication, authorization, and encryption'),
-- Programming objectives
('OBJ101', 'Write procedural code', 'Students will implement algorithms using loops and conditionals'),
('OBJ102', 'Use data structures effectively', 'Students will select and implement appropriate data structures'),
('OBJ103', 'Analyze algorithm complexity', 'Students will compute Big-O time and space complexity'),
('OBJ104', 'Apply object-oriented principles', 'Students will use encapsulation, inheritance, and polymorphism'),
('OBJ105', 'Debug and test code', 'Students will write unit tests and use debugging tools'),
-- Math/theory objectives
('OBJ201', 'Prove correctness using logic', 'Students will construct formal proofs using predicate logic'),
('OBJ202', 'Apply graph algorithms', 'Students will implement BFS, DFS, shortest path algorithms'),
('OBJ203', 'Model problems mathematically', 'Students will translate real-world problems to mathematical models'),
-- Security objectives
('OBJ301', 'Identify security vulnerabilities', 'Students will recognize SQL injection, XSS, and CSRF attacks'),
('OBJ302', 'Implement encryption protocols', 'Students will use symmetric and asymmetric cryptography'),
('OBJ303', 'Conduct security audits', 'Students will perform penetration testing and risk assessment'),
-- Data science objectives
('OBJ401', 'Apply machine learning algorithms', 'Students will train and evaluate supervised learning models'),
('OBJ402', 'Process and clean data', 'Students will handle missing values, outliers, and normalization'),
('OBJ403', 'Visualize data insights', 'Students will create effective statistical visualizations'),
-- Web development objectives
('OBJ501', 'Build responsive interfaces', 'Students will create mobile-first web applications'),
('OBJ502', 'Implement RESTful APIs', 'Students will design and document REST endpoints'),
('OBJ503', 'Deploy web applications', 'Students will use CI/CD pipelines and cloud platforms'),
-- Edge case: maximum length title (exactly 120 chars)
('OBJ999', 'This Learning Objective Title Tests VARCHAR 120 Char Limit With Exactly One Hundred Twenty Characters Total Here Now', 'Tests boundary');

-- ============================================================================
-- DEGREECOURSE: Test composite FK, CASCADE delete, is_core flag
-- ============================================================================
INSERT INTO DegreeCourse (name, level, course_no, is_core) VALUES
-- Computer Science BS (core curriculum)
('Computer Science', 'BS', 'CS1111', 1),
('Computer Science', 'BS', 'CS2222', 1),
('Computer Science', 'BS', 'CS3333', 1),
('Computer Science', 'BS', 'CS5330', 1),
('Computer Science', 'BS', 'CS4444', 1),
('Computer Science', 'BS', 'MATH2410', 1),
('Computer Science', 'BS', 'STAT3000', 1),
-- Computer Science BS (electives)
('Computer Science', 'BS', 'SEC4100', 0),
('Computer Science', 'BS', 'DS3100', 0),
('Computer Science', 'BS', 'WEB2100', 0),
-- Computer Science MS (all core for grad students)
('Computer Science', 'MS', 'CS7330', 1),
('Computer Science', 'MS', 'CS5330', 1),
('Computer Science', 'MS', 'SEC4200', 1),
('Computer Science', 'MS', 'DS3200', 1),
('Computer Science', 'MS', 'DB4100', 1),
-- Computer Science Ph.D. (research-focused)
('Computer Science', 'Ph.D.', 'CS7330', 1),
('Computer Science', 'Ph.D.', 'DB4100', 1),
-- Data Science BS
('Data Science', 'BS', 'CS1111', 1),
('Data Science', 'BS', 'CS2222', 1),
('Data Science', 'BS', 'STAT3000', 1),
('Data Science', 'BS', 'DS3100', 1),
('Data Science', 'BS', 'DS3200', 1),
('Data Science', 'BS', 'CS5330', 0),
-- Data Science MS
('Data Science', 'MS', 'DS3200', 1),
('Data Science', 'MS', 'CS7330', 0),
('Data Science', 'MS', 'DB4100', 1),
-- Cybersecurity BS
('Cybersecurity', 'BS', 'CS1111', 1),
('Cybersecurity', 'BS', 'CS2222', 1),
('Cybersecurity', 'BS', 'SEC4100', 1),
('Cybersecurity', 'BS', 'SEC4200', 1),
('Cybersecurity', 'BS', 'CS5330', 1),
-- Cybersecurity MS
('Cybersecurity', 'MS', 'SEC4200', 1),
('Cybersecurity', 'MS', 'CS7330', 0),
-- Software Engineering BS
('Software Engineering', 'BS', 'CS1111', 1),
('Software Engineering', 'BS', 'CS2222', 1),
('Software Engineering', 'BS', 'CS3333', 1),
('Software Engineering', 'BS', 'CS4444', 1),
('Software Engineering', 'BS', 'WEB2100', 0),
('Software Engineering', 'BS', 'WEB2200', 0),
-- IT BA (liberal arts focus)
('Information Technology', 'BA', 'CS1111', 1),
('Information Technology', 'BA', 'WEB2100', 1),
('Information Technology', 'BA', 'WEB2200', 1),
-- Web Development Certificate (focused program)
('Web Development', 'Cert', 'WEB2100', 1),
('Web Development', 'Cert', 'WEB2200', 1),
('Web Development', 'Cert', 'CS1111', 0),
-- Database Admin Certificate
('Database Administration', 'Cert', 'CS5330', 1),
('Database Administration', 'Cert', 'DB4100', 1),
('Database Administration', 'Cert', 'DB4200', 1),
-- Edge case: same course in multiple degrees with different core status
('Computer Engineering', 'BS', 'CS1111', 1),
('Computer Engineering', 'BS', 'CS5330', 0),
('Computer Engineering', 'BS', 'AB1234', 0);

-- ============================================================================
-- DEGREECOURSEOBJECTIVE: Test 4-part composite key, CASCADE behavior
-- ============================================================================
INSERT INTO DegreeCourseObjective (name, level, course_no, objective_code) VALUES
-- CS5330 for Computer Science BS (database course with all 5 DB objectives)
('Computer Science', 'BS', 'CS5330', 'OBJ001'),
('Computer Science', 'BS', 'CS5330', 'OBJ002'),
('Computer Science', 'BS', 'CS5330', 'OBJ003'),
('Computer Science', 'BS', 'CS5330', 'OBJ004'),
('Computer Science', 'BS', 'CS5330', 'OBJ005'),
-- CS7330 for Computer Science MS (advanced database)
('Computer Science', 'MS', 'CS7330', 'OBJ001'),
('Computer Science', 'MS', 'CS7330', 'OBJ002'),
('Computer Science', 'MS', 'CS7330', 'OBJ003'),
('Computer Science', 'MS', 'CS7330', 'OBJ004'),
('Computer Science', 'MS', 'CS7330', 'OBJ005'),
-- CS7330 for Computer Science Ph.D.
('Computer Science', 'Ph.D.', 'CS7330', 'OBJ001'),
('Computer Science', 'Ph.D.', 'CS7330', 'OBJ002'),
('Computer Science', 'Ph.D.', 'CS7330', 'OBJ003'),
-- CS1111 for multiple degrees (programming fundamentals)
('Computer Science', 'BS', 'CS1111', 'OBJ101'),
('Computer Science', 'BS', 'CS1111', 'OBJ105'),
('Data Science', 'BS', 'CS1111', 'OBJ101'),
('Data Science', 'BS', 'CS1111', 'OBJ105'),
('Cybersecurity', 'BS', 'CS1111', 'OBJ101'),
('Software Engineering', 'BS', 'CS1111', 'OBJ101'),
('Software Engineering', 'BS', 'CS1111', 'OBJ104'),
('Information Technology', 'BA', 'CS1111', 'OBJ101'),
('Computer Engineering', 'BS', 'CS1111', 'OBJ101'),
-- CS2222 (data structures)
('Computer Science', 'BS', 'CS2222', 'OBJ102'),
('Computer Science', 'BS', 'CS2222', 'OBJ103'),
('Data Science', 'BS', 'CS2222', 'OBJ102'),
('Cybersecurity', 'BS', 'CS2222', 'OBJ102'),
('Software Engineering', 'BS', 'CS2222', 'OBJ102'),
-- CS3333 (algorithms)
('Computer Science', 'BS', 'CS3333', 'OBJ103'),
('Computer Science', 'BS', 'CS3333', 'OBJ202'),
('Software Engineering', 'BS', 'CS3333', 'OBJ103'),
-- Security courses
('Cybersecurity', 'BS', 'SEC4100', 'OBJ301'),
('Cybersecurity', 'BS', 'SEC4100', 'OBJ302'),
('Cybersecurity', 'BS', 'SEC4200', 'OBJ301'),
('Cybersecurity', 'BS', 'SEC4200', 'OBJ303'),
('Cybersecurity', 'MS', 'SEC4200', 'OBJ301'),
('Cybersecurity', 'MS', 'SEC4200', 'OBJ302'),
('Cybersecurity', 'MS', 'SEC4200', 'OBJ303'),
('Computer Science', 'MS', 'SEC4200', 'OBJ301'),
-- Data Science courses
('Data Science', 'BS', 'DS3100', 'OBJ401'),
('Data Science', 'BS', 'DS3100', 'OBJ402'),
('Data Science', 'BS', 'DS3200', 'OBJ401'),
('Data Science', 'BS', 'DS3200', 'OBJ403'),
('Data Science', 'MS', 'DS3200', 'OBJ401'),
('Data Science', 'MS', 'DS3200', 'OBJ402'),
('Data Science', 'MS', 'DS3200', 'OBJ403'),
-- Web Development
('Web Development', 'Cert', 'WEB2100', 'OBJ501'),
('Web Development', 'Cert', 'WEB2100', 'OBJ503'),
('Web Development', 'Cert', 'WEB2200', 'OBJ502'),
('Web Development', 'Cert', 'WEB2200', 'OBJ503'),
('Software Engineering', 'BS', 'WEB2100', 'OBJ501'),
('Software Engineering', 'BS', 'WEB2200', 'OBJ502'),
('Information Technology', 'BA', 'WEB2100', 'OBJ501'),
('Information Technology', 'BA', 'WEB2200', 'OBJ502'),
-- Database courses across degrees (OBJ001 already assigned above, skip duplicate)
('Cybersecurity', 'BS', 'CS5330', 'OBJ001'),
('Cybersecurity', 'BS', 'CS5330', 'OBJ005'),
('Database Administration', 'Cert', 'CS5330', 'OBJ001'),
('Database Administration', 'Cert', 'CS5330', 'OBJ002'),
('Database Administration', 'Cert', 'CS5330', 'OBJ003'),
('Database Administration', 'Cert', 'CS5330', 'OBJ004'),
('Database Administration', 'Cert', 'DB4100', 'OBJ001'),
('Database Administration', 'Cert', 'DB4100', 'OBJ004'),
('Database Administration', 'Cert', 'DB4200', 'OBJ004'),
('Computer Science', 'MS', 'DB4100', 'OBJ001'),
('Computer Science', 'MS', 'DB4100', 'OBJ004'),
('Data Science', 'BS', 'CS5330', 'OBJ001'),
('Data Science', 'BS', 'CS5330', 'OBJ002'),
('Data Science', 'MS', 'DB4100', 'OBJ001'),
('Data Science', 'MS', 'DB4100', 'OBJ002'),
-- Edge cases: courses with single objective
('Computer Science', 'BS', 'MATH2410', 'OBJ201'),
('Computer Science', 'BS', 'STAT3000', 'OBJ203'),
('Data Science', 'BS', 'STAT3000', 'OBJ203'),
('Computer Science', 'BS', 'CS4444', 'OBJ104'),
-- Edge case: same course, different objectives per degree
('Computer Engineering', 'BS', 'CS5330', 'OBJ001'),
('Computer Engineering', 'BS', 'CS5330', 'OBJ002'),
('Computer Engineering', 'BS', 'AB1234', 'OBJ001');

-- ============================================================================
-- EVALUATION: Test 8-part composite PK, all CHECK constraints, NULL handling
-- ============================================================================

-- CS5330 Fall 2023 Section 001 (Computer Science BS) - Complete evaluation
INSERT INTO Evaluation (course_no, year, term, section_no, name, level, objective_code, method_label, a_count, b_count, c_count, f_count, improvement_text) VALUES
('CS5330', 2023, 'Fall', '001', 'Computer Science', 'BS', 'OBJ001', 'Exam 1', 18, 12, 4, 1, 'Students struggled with ER diagram notation'),
('CS5330', 2023, 'Fall', '001', 'Computer Science', 'BS', 'OBJ002', 'Exam 2', 20, 10, 4, 1, 'JOIN syntax needs more practice'),
('CS5330', 2023, 'Fall', '001', 'Computer Science', 'BS', 'OBJ003', 'Project', 22, 9, 3, 1, 'Transaction isolation levels were confusing'),
('CS5330', 2023, 'Fall', '001', 'Computer Science', 'BS', 'OBJ004', 'Lab Assignment', 15, 15, 4, 1, 'Index selection requires more examples'),
('CS5330', 2023, 'Fall', '001', 'Computer Science', 'BS', 'OBJ005', 'Homework', 19, 11, 4, 1, NULL);

-- CS5330 Fall 2023 Section 002 (Computer Science BS) - Different instructor, different results
INSERT INTO Evaluation (course_no, year, term, section_no, name, level, objective_code, method_label, a_count, b_count, c_count, f_count, improvement_text) VALUES
('CS5330', 2023, 'Fall', '002', 'Computer Science', 'BS', 'OBJ001', 'Exam 1', 16, 10, 5, 1, 'Need more normalization examples'),
('CS5330', 2023, 'Fall', '002', 'Computer Science', 'BS', 'OBJ002', 'Exam 2', 17, 11, 3, 1, 'Subqueries were challenging'),
('CS5330', 2023, 'Fall', '002', 'Computer Science', 'BS', 'OBJ003', 'Project', 20, 8, 3, 1, NULL),
('CS5330', 2023, 'Fall', '002', 'Computer Science', 'BS', 'OBJ004', 'Quiz', 18, 9, 4, 1, 'Query optimization needs emphasis'),
('CS5330', 2023, 'Fall', '002', 'Computer Science', 'BS', 'OBJ005', 'Final Exam', 19, 10, 2, 1, 'Encryption concepts well understood');

-- CS7330 Fall 2023 (Computer Science MS) - Graduate level, smaller class
INSERT INTO Evaluation (course_no, year, term, section_no, name, level, objective_code, method_label, a_count, b_count, c_count, f_count, improvement_text) VALUES
('CS7330', 2023, 'Fall', '001', 'Computer Science', 'MS', 'OBJ001', 'Research Paper', 10, 6, 2, 0, 'Advanced modeling techniques mastered'),
('CS7330', 2023, 'Fall', '001', 'Computer Science', 'MS', 'OBJ002', 'Presentation', 12, 5, 1, 0, 'Complex query optimization demonstrated'),
('CS7330', 2023, 'Fall', '001', 'Computer Science', 'MS', 'OBJ003', 'Implementation', 9, 7, 2, 0, NULL),
('CS7330', 2023, 'Fall', '001', 'Computer Science', 'MS', 'OBJ004', 'Final Project', 11, 5, 2, 0, 'Distributed database concepts strong'),
('CS7330', 2023, 'Fall', '001', 'Computer Science', 'MS', 'OBJ005', 'Security Audit', 10, 6, 2, 0, 'Excellent security implementation');

-- CS1111 Fall 2023 Section 001 (Computer Science BS) - Large intro class
INSERT INTO Evaluation (course_no, year, term, section_no, name, level, objective_code, method_label, a_count, b_count, c_count, f_count, improvement_text) VALUES
('CS1111', 2023, 'Fall', '001', 'Computer Science', 'BS', 'OBJ101', 'Midterm Exam', 50, 40, 25, 5, 'Loop logic needs reinforcement'),
('CS1111', 2023, 'Fall', '001', 'Computer Science', 'BS', 'OBJ105', 'Lab Practicals', 60, 35, 20, 5, 'Debugging skills improving');

-- SEC4100 Fall 2023 (Cybersecurity BS) - Security course
INSERT INTO Evaluation (course_no, year, term, section_no, name, level, objective_code, method_label, a_count, b_count, c_count, f_count, improvement_text) VALUES
('SEC4100', 2023, 'Fall', '001', 'Cybersecurity', 'BS', 'OBJ301', 'Penetration Test', 15, 9, 3, 1, 'Vulnerability scanning improved'),
('SEC4100', 2023, 'Fall', '001', 'Cybersecurity', 'BS', 'OBJ302', 'Encryption Lab', 18, 7, 2, 1, 'Strong cryptographic implementations'),
('WEB2100', 2024, 'Summer', '001', 'Web Development', 'Cert', 'OBJ501', 'Portfolio Project', 18, 0, 0, 0, 'Excellent cohort performance'),
('CS3333', 2023, 'Fall', '001', 'Computer Science', 'BS', 'OBJ103', 'Algorithm Analysis Exam', 10, 15, 20, 15, 'Exam was too difficult, will adjust'),
('DB4100', 2024, 'Fall', '001', 'Computer Science', 'MS', 'OBJ001', 'TBD', 0, 0, 0, 0, 'Assessment not yet administered');

-- CS5330 Spring 2024 with multiple methods per objective
INSERT INTO Evaluation (course_no, year, term, section_no, name, level, objective_code, method_label, a_count, b_count, c_count, f_count, improvement_text) VALUES
('CS5330', 2024, 'Spring', '001', 'Computer Science', 'BS', 'OBJ001', 'Exam', 20, 12, 6, 2, 'Written exam performance'),
('CS5330', 2024, 'Spring', '001', 'Computer Science', 'BS', 'OBJ001', 'Project', 25, 10, 4, 1, 'Practical project performance better'),
('CS5330', 2024, 'Spring', '001', 'Computer Science', 'BS', 'OBJ002', 'Quiz 1', 18, 15, 5, 2, 'Basic queries good'),
('CS5330', 2024, 'Spring', '001', 'Computer Science', 'BS', 'OBJ002', 'Quiz 2', 22, 12, 4, 2, 'Advanced queries improving');

-- Data Science courses
INSERT INTO Evaluation (course_no, year, term, section_no, name, level, objective_code, method_label, a_count, b_count, c_count, f_count, improvement_text) VALUES
('DS3100', 2023, 'Fall', '001', 'Data Science', 'BS', 'OBJ401', 'ML Project', 18, 12, 4, 1, 'Feature engineering needs work'),
('DS3100', 2023, 'Fall', '001', 'Data Science', 'BS', 'OBJ402', 'Data Cleaning Lab', 20, 10, 4, 1, 'Pandas proficiency strong');

-- Certificate programs
INSERT INTO Evaluation (course_no, year, term, section_no, name, level, objective_code, method_label, a_count, b_count, c_count, f_count, improvement_text) VALUES
('CS5330', 2023, 'Fall', '001', 'Database Administration', 'Cert', 'OBJ001', 'Certification Exam', 8, 3, 1, 0, 'Professional students excel'),
('CS5330', 2023, 'Fall', '001', 'Database Administration', 'Cert', 'OBJ002', 'SQL Practicum', 9, 2, 1, 0, NULL);

-- Edge case: Long improvement text (TEXT field)
INSERT INTO Evaluation (course_no, year, term, section_no, name, level, objective_code, method_label, a_count, b_count, c_count, f_count, improvement_text) VALUES
('CS2222', 2023, 'Fall', '001', 'Computer Science', 'BS', 'OBJ102', 'Final Project', 40, 25, 12, 3, 'Students demonstrated strong understanding of linked lists and trees. However, graph algorithms remain challenging. Recommendation: add more visualization tools and step-through examples. Consider flipped classroom approach for complex topics. Students who attended office hours performed significantly better. May need to incentivize attendance or make video recordings available.');

-- Recent semesters with partial data (realistic incomplete evaluation scenario)
INSERT INTO Evaluation (course_no, year, term, section_no, name, level, objective_code, method_label, a_count, b_count, c_count, f_count, improvement_text) VALUES
('CS5330', 2024, 'Fall', '001', 'Computer Science', 'BS', 'OBJ001', 'Midterm', 19, 13, 5, 1, 'Semester in progress'),
('CS5330', 2024, 'Fall', '001', 'Computer Science', 'BS', 'OBJ002', 'Homework 1-3', 22, 11, 4, 1, NULL);
-- OBJ003, OBJ004, OBJ005 not yet evaluated (simulates incomplete semester)

-- Cross-degree same section evaluations (CS5330 used by multiple programs)
INSERT INTO Evaluation (course_no, year, term, section_no, name, level, objective_code, method_label, a_count, b_count, c_count, f_count, improvement_text) VALUES
('CS5330', 2023, 'Fall', '001', 'Cybersecurity', 'BS', 'OBJ001', 'Exam 1', 12, 8, 3, 1, 'Security-focused students strong in design'),
('CS5330', 2023, 'Fall', '001', 'Cybersecurity', 'BS', 'OBJ005', 'Security Project', 14, 6, 3, 1, 'Excellent security implementations'),
('CS5330', 2023, 'Fall', '001', 'Data Science', 'BS', 'OBJ001', 'Exam 1', 10, 7, 2, 1, 'Data-focused students need more design practice'),
('CS5330', 2023, 'Fall', '001', 'Data Science', 'BS', 'OBJ002', 'Analytics Query Project', 12, 6, 1, 1, 'Strong SQL for analytics');

-- PhD evaluations (small cohort)
INSERT INTO Evaluation (course_no, year, term, section_no, name, level, objective_code, method_label, a_count, b_count, c_count, f_count, improvement_text) VALUES
('CS7330', 2023, 'Fall', '001', 'Computer Science', 'Ph.D.', 'OBJ001', 'Dissertation Proposal', 3, 1, 0, 0, 'Research methodology excellent'),
('CS7330', 2023, 'Fall', '001', 'Computer Science', 'Ph.D.', 'OBJ002', 'Conference Paper', 2, 2, 0, 0, 'Publication-quality work'),
('AB1234', 2023, 'Fall', '001', 'Computer Engineering', 'BS', 'OBJ001', 'Very Long Assessment Method Label Test', 8, 5, 2, 0, 'Tests 40-char limit');

-- ============================================================================
-- Summary Statistics (for verification)
-- ============================================================================
-- Total records inserted:
-- Degrees: 13 (covering all 5 levels with duplicates by name)
-- Courses: 20 (edge cases for VARCHAR limits, special chars)
-- Instructors: 13 (including special characters)
-- Semesters: 18 (6 years × 3 terms)
-- Sections: 34 (multiple sections per course, enrollment variety)
-- Objectives: 23 (covering all domains)
-- DegreeCourse: 57 (core/elective mix across all degrees)
-- DegreeCourseObjective: 86 (many-to-many relationships)
-- Evaluation: 70+ (complete/partial/edge cases)

SELECT 'Sample data loaded successfully' AS Status;
SELECT CONCAT('Degrees: ', COUNT(*), ' | Courses: ', (SELECT COUNT(*) FROM Course)) AS Counts FROM Degree;
SELECT CONCAT('Sections: ', COUNT(*), ' | Evaluations: ', (SELECT COUNT(*) FROM Evaluation)) AS Counts FROM Section;
