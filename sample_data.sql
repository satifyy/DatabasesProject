USE curriculum_tracker;

INSERT INTO Degree (name, level, description) VALUES
    ('Computer Science', 'Bachelors', 'Four-year program focused on algorithms, systems, and software.'),
    ('Data Science', 'Masters', 'Graduate program in applied machine learning and analytics.');

INSERT INTO Course (course_no, title, description) VALUES
    ('CS101', 'Intro to Programming', 'Fundamentals of programming and computational thinking.'),
    ('CS201', 'Data Structures', 'Intermediate course on abstract data types and algorithms.'),
    ('DS510', 'Machine Learning Studio', 'Project-based course emphasizing modeling and deployment.'),
    ('DS520', 'Data Warehousing', 'Covers ETL processes and OLAP design.');

INSERT INTO Instructor (instructor_id, name) VALUES
    ('I001', 'Dr. Ada Byron'),
    ('I002', 'Dr. Alan Turing'),
    ('I003', 'Dr. Grace Hopper');

INSERT INTO Semester (year, term) VALUES
    (2023, 'Fall'),
    (2024, 'Spring'),
    (2024, 'Fall');

INSERT INTO Section (course_no, year, term, section_no, instructor_id, enrolled_count) VALUES
    ('CS101', 2024, 'Spring', '01', 'I001', 45),
    ('CS201', 2024, 'Spring', '01', 'I002', 35),
    ('DS510', 2024, 'Fall', '01', 'I002', 20),
    ('DS520', 2024, 'Fall', '02', 'I003', 18),
    ('CS201', 2023, 'Fall', '02', 'I001', 30);

INSERT INTO Objective (code, title, description) VALUES
    ('OBJ1', 'Problem Solving', 'Apply algorithmic thinking to novel problems.'),
    ('OBJ2', 'Algorithm Analysis', 'Analyze complexity and performance.'),
    ('OBJ3', 'Data Management', 'Design and evaluate storage solutions.'),
    ('OBJ4', 'Communication', 'Communicate technical ideas clearly.');

INSERT INTO DegreeCourse (name, level, course_no, is_core) VALUES
    ('Computer Science', 'Bachelors', 'CS101', 1),
    ('Computer Science', 'Bachelors', 'CS201', 1),
    ('Computer Science', 'Bachelors', 'DS520', 0),
    ('Data Science', 'Masters', 'CS201', 0),
    ('Data Science', 'Masters', 'DS510', 1),
    ('Data Science', 'Masters', 'DS520', 1);

INSERT INTO DegreeCourseObjective (name, level, course_no, objective_code) VALUES
    ('Computer Science', 'Bachelors', 'CS101', 'OBJ1'),
    ('Computer Science', 'Bachelors', 'CS101', 'OBJ4'),
    ('Computer Science', 'Bachelors', 'CS201', 'OBJ1'),
    ('Computer Science', 'Bachelors', 'CS201', 'OBJ2'),
    ('Computer Science', 'Bachelors', 'DS520', 'OBJ3'),
    ('Data Science', 'Masters', 'CS201', 'OBJ2'),
    ('Data Science', 'Masters', 'DS510', 'OBJ3'),
    ('Data Science', 'Masters', 'DS510', 'OBJ4'),
    ('Data Science', 'Masters', 'DS520', 'OBJ1'),
    ('Data Science', 'Masters', 'DS520', 'OBJ3');

INSERT INTO Evaluation (
    course_no, year, term, section_no, name, level, objective_code,
    method_label, a_count, b_count, c_count, f_count, improvement_text
) VALUES
    ('CS101', 2024, 'Spring', '01', 'Computer Science', 'Bachelors', 'OBJ1',
        'Final Exam', 20, 15, 5, 5, 'Add more peer programming practice.'),
    ('CS101', 2024, 'Spring', '01', 'Computer Science', 'Bachelors', 'OBJ4',
        'Presentation', 18, 12, NULL, NULL, NULL),
    ('DS510', 2024, 'Fall', '01', 'Data Science', 'Masters', 'OBJ3',
        'Capstone', 8, 7, 4, 1, 'Invite more industry mentors.'),
    ('DS520', 2024, 'Fall', '02', 'Data Science', 'Masters', 'OBJ1',
        'Case Study', 10, 5, 2, 1, NULL);
