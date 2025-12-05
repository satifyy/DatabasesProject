<?php
declare(strict_types=1);

require_once __DIR__ . '/db.php';
session_start();

$messages = [];
$errors = [];
$degreeQueryData = null;
$courseQueryData = null;
$instructorQueryData = null;
$evalStatusData = null;
$nonfData = null;

$TERM_OPTIONS = ['Spring', 'Summer', 'Fall'];

function term_order(string $term): int
{
    static $map = ['Spring' => 1, 'Summer' => 2, 'Fall' => 3];
    return $map[$term] ?? 0;
}

function parse_semester_label(string $label): ?array
{
    if (strpos($label, '-') === false) {
        return null;
    }
    [$year, $term] = explode('-', $label, 2);
    return ['year' => (int)$year, 'term' => $term];
}

function semester_in_range(int $year, string $term, string $startLabel, string $endLabel): bool
{
    $start = parse_semester_label($startLabel) ?? ['year' => 0, 'term' => 'Spring'];
    $end = parse_semester_label($endLabel) ?? ['year' => 9999, 'term' => 'Fall'];
    $currentVal = ($year * 10) + term_order($term);
    $startVal = ($start['year'] * 10) + term_order($start['term']);
    $endVal = ($end['year'] * 10) + term_order($end['term']);
    return $currentVal >= $startVal && $currentVal <= $endVal;
}

function h(null|string|int|float $value): string
{
    return htmlspecialchars((string)($value ?? ''), ENT_QUOTES);
}

$mutationActions = [
    'save_degree',
    'delete_degree',
    'save_course',
    'delete_course',
    'save_instructor',
    'delete_instructor',
    'save_semester',
    'delete_semester',
    'save_objective',
    'delete_objective',
    'assign_degree_course',
    'remove_degree_course',
    'assign_dco',
    'remove_dco',
    'add_section',
    'save_evaluation',
    'copy_evaluation',
];

$action = $_POST['action'] ?? '';
$pdo = null;

try {
    if ($_SERVER['REQUEST_METHOD'] === 'POST' && $action) {
        $pdo = get_db_connection();
        $isMutation = in_array($action, $mutationActions, true);
        if ($isMutation) {
            $pdo->beginTransaction();
        }

        switch ($action) {
            case 'save_degree':
                $name = trim($_POST['degree_name'] ?? '');
                $level = trim($_POST['degree_level'] ?? '');
                $description = trim($_POST['degree_description'] ?? '');
                if (!$name || !$level) {
                    throw new RuntimeException('Degree name and level are required.');
                }
                $stmt = $pdo->prepare('INSERT INTO Degree(name, level, description) VALUES (?,?,?)
                    ON DUPLICATE KEY UPDATE description=VALUES(description)');
                $stmt->execute([$name, $level, $description ?: null]);
                $messages[] = "Degree saved for {$name} ({$level}).";
                break;
            case 'delete_degree':
                $name = trim($_POST['degree_name'] ?? '');
                $level = trim($_POST['degree_level'] ?? '');
                $stmt = $pdo->prepare('DELETE FROM Degree WHERE name=? AND level=?');
                $stmt->execute([$name, $level]);
                $messages[] = "Degree {$name} ({$level}) deleted.";
                break;
            case 'save_course':
                $courseNo = trim($_POST['course_no'] ?? '');
                $title = trim($_POST['course_title'] ?? '');
                $description = trim($_POST['course_description'] ?? '');
                if (!$courseNo || !$title) {
                    throw new RuntimeException('Course number and title are required.');
                }
                $stmt = $pdo->prepare('INSERT INTO Course(course_no, title, description) VALUES (?,?,?)
                    ON DUPLICATE KEY UPDATE title=VALUES(title), description=VALUES(description)');
                $stmt->execute([$courseNo, $title, $description ?: null]);
                $messages[] = "Course {$courseNo} saved.";
                break;
            case 'delete_course':
                $courseNo = trim($_POST['course_no'] ?? '');
                $stmt = $pdo->prepare('DELETE FROM Course WHERE course_no=?');
                $stmt->execute([$courseNo]);
                $messages[] = "Course {$courseNo} deleted.";
                break;
            case 'save_instructor':
                $instructorId = trim($_POST['instructor_id'] ?? '');
                $name = trim($_POST['instructor_name'] ?? '');
                if (!$instructorId || !$name) {
                    throw new RuntimeException('Instructor ID and name are required.');
                }
                $stmt = $pdo->prepare('INSERT INTO Instructor(instructor_id, name) VALUES (?,?)
                    ON DUPLICATE KEY UPDATE name=VALUES(name)');
                $stmt->execute([$instructorId, $name]);
                $messages[] = "Instructor {$instructorId} saved.";
                break;
            case 'delete_instructor':
                $instructorId = trim($_POST['instructor_id'] ?? '');
                $stmt = $pdo->prepare('DELETE FROM Instructor WHERE instructor_id=?');
                $stmt->execute([$instructorId]);
                $messages[] = "Instructor {$instructorId} deleted.";
                break;
            case 'save_semester':
                $year = (int)($_POST['semester_year'] ?? 0);
                $term = $_POST['semester_term'] ?? '';
                if (!$year || !$term) {
                    throw new RuntimeException('Semester year and term are required.');
                }
                $stmt = $pdo->prepare('INSERT INTO Semester(year, term) VALUES (?,?)
                    ON DUPLICATE KEY UPDATE term=VALUES(term)');
                $stmt->execute([$year, $term]);
                $messages[] = "Semester {$year} {$term} saved.";
                break;
            case 'delete_semester':
                $year = (int)($_POST['semester_year'] ?? 0);
                $term = $_POST['semester_term'] ?? '';
                $stmt = $pdo->prepare('DELETE FROM Semester WHERE year=? AND term=?');
                $stmt->execute([$year, $term]);
                $messages[] = "Semester {$year} {$term} deleted.";
                break;
            case 'save_objective':
                $code = trim($_POST['objective_code'] ?? '');
                $title = trim($_POST['objective_title'] ?? '');
                $description = trim($_POST['objective_description'] ?? '');
                if (!$code || !$title) {
                    throw new RuntimeException('Objective code and title are required.');
                }
                $stmt = $pdo->prepare('INSERT INTO Objective(code, title, description) VALUES (?,?,?)
                    ON DUPLICATE KEY UPDATE title=VALUES(title), description=VALUES(description)');
                $stmt->execute([$code, $title, $description ?: null]);
                $messages[] = "Objective {$code} saved.";
                break;
            case 'delete_objective':
                $code = trim($_POST['objective_code'] ?? '');
                $stmt = $pdo->prepare('DELETE FROM Objective WHERE code=?');
                $stmt->execute([$code]);
                $messages[] = "Objective {$code} deleted.";
                break;
            case 'assign_degree_course':
                $name = trim($_POST['degree_name'] ?? '');
                $level = trim($_POST['degree_level'] ?? '');
                $courseNo = trim($_POST['course_no'] ?? '');
                $isCore = isset($_POST['is_core']) ? 1 : 0;
                if (!$name || !$level || !$courseNo) {
                    throw new RuntimeException('Degree and course are required.');
                }
                $stmt = $pdo->prepare('SELECT is_core FROM DegreeCourse WHERE name=? AND level=? AND course_no=?');
                $stmt->execute([$name, $level, $courseNo]);
                $existing = $stmt->fetchColumn();
                if ((int)$existing === 1 && $isCore === 0) {
                    $countStmt = $pdo->prepare('SELECT COUNT(*) FROM DegreeCourse WHERE name=? AND level=? AND is_core=1 AND course_no <> ?');
                    $countStmt->execute([$name, $level, $courseNo]);
                    if ((int)$countStmt->fetchColumn() === 0) {
                        throw new RuntimeException('Each degree must keep at least one core course.');
                    }
                }
                if ($isCore === 1) {
                    $objStmt = $pdo->prepare('SELECT COUNT(*) FROM DegreeCourseObjective WHERE name=? AND level=? AND course_no=?');
                    $objStmt->execute([$name, $level, $courseNo]);
                    if ((int)$objStmt->fetchColumn() === 0) {
                        throw new RuntimeException('Add at least one objective before marking the course as core.');
                    }
                }
                $stmt = $pdo->prepare('INSERT INTO DegreeCourse(name, level, course_no, is_core) VALUES (?,?,?,?)
                    ON DUPLICATE KEY UPDATE is_core=VALUES(is_core)');
                $stmt->execute([$name, $level, $courseNo, $isCore]);
                $messages[] = 'Degree-course link saved.';
                break;
            case 'remove_degree_course':
                $name = trim($_POST['degree_name'] ?? '');
                $level = trim($_POST['degree_level'] ?? '');
                $courseNo = trim($_POST['course_no'] ?? '');
                if (!$name || !$level || !$courseNo) {
                    throw new RuntimeException('Degree and course are required.');
                }
                $stmt = $pdo->prepare('SELECT is_core FROM DegreeCourse WHERE name=? AND level=? AND course_no=?');
                $stmt->execute([$name, $level, $courseNo]);
                $isCore = $stmt->fetchColumn();
                if ($isCore === false) {
                    break;
                }
                if ((int)$isCore === 1) {
                    $countStmt = $pdo->prepare('SELECT COUNT(*) FROM DegreeCourse WHERE name=? AND level=? AND is_core=1');
                    $countStmt->execute([$name, $level]);
                    if ((int)$countStmt->fetchColumn() <= 1) {
                        throw new RuntimeException('Cannot remove the last core course from a degree.');
                    }
                }
                $del = $pdo->prepare('DELETE FROM DegreeCourse WHERE name=? AND level=? AND course_no=?');
                $del->execute([$name, $level, $courseNo]);
                $messages[] = 'Degree-course link removed.';
                break;
            case 'assign_dco':
                $name = trim($_POST['degree_name'] ?? '');
                $level = trim($_POST['degree_level'] ?? '');
                $courseNo = trim($_POST['course_no'] ?? '');
                $objective = trim($_POST['objective_code'] ?? '');
                if (!$name || !$level || !$courseNo || !$objective) {
                    throw new RuntimeException('Complete the degree, course, and objective selection.');
                }
                $stmt = $pdo->prepare('INSERT INTO DegreeCourseObjective(name, level, course_no, objective_code) VALUES (?,?,?,?)
                    ON DUPLICATE KEY UPDATE objective_code=objective_code');
                $stmt->execute([$name, $level, $courseNo, $objective]);
                $messages[] = 'Objective linked to course.';
                break;
            case 'remove_dco':
                $name = trim($_POST['degree_name'] ?? '');
                $level = trim($_POST['degree_level'] ?? '');
                $courseNo = trim($_POST['course_no'] ?? '');
                $objective = trim($_POST['objective_code'] ?? '');
                if (!$name || !$level || !$courseNo || !$objective) {
                    throw new RuntimeException('Complete the degree, course, and objective selection.');
                }
                $coreStmt = $pdo->prepare('SELECT is_core FROM DegreeCourse WHERE name=? AND level=? AND course_no=?');
                $coreStmt->execute([$name, $level, $courseNo]);
                $isCore = (int)$coreStmt->fetchColumn();
                if ($isCore === 1) {
                    $objCountStmt = $pdo->prepare('SELECT COUNT(*) FROM DegreeCourseObjective WHERE name=? AND level=? AND course_no=?');
                    $objCountStmt->execute([$name, $level, $courseNo]);
                    if ((int)$objCountStmt->fetchColumn() <= 1) {
                        throw new RuntimeException('Core courses must keep at least one objective.');
                    }
                }
                $degreeObjCount = $pdo->prepare('SELECT COUNT(*) FROM DegreeCourseObjective WHERE name=? AND level=? AND objective_code=? AND NOT (course_no=? AND objective_code=?)');
                $degreeObjCount->execute([$name, $level, $objective, $courseNo, $objective]);
                if ((int)$degreeObjCount->fetchColumn() === 0) {
                    throw new RuntimeException('Each objective must remain tied to at least one course for the degree.');
                }
                $stmt = $pdo->prepare('DELETE FROM DegreeCourseObjective WHERE name=? AND level=? AND course_no=? AND objective_code=?');
                $stmt->execute([$name, $level, $courseNo, $objective]);
                $messages[] = 'Objective removed from course.';
                break;
            case 'add_section':
                $courseNo = $_POST['section_course'] ?? '';
                $semester = explode('|', $_POST['section_semester'] ?? '');
                if (count($semester) !== 2) {
                    throw new RuntimeException('Select a semester.');
                }
                [$year, $term] = $semester;
                $sectionNo = trim($_POST['section_no'] ?? '');
                $instructor = $_POST['section_instructor'] ?? '';
                $enrolled = (int)($_POST['section_enrolled'] ?? 0);
                if (!$courseNo || !$sectionNo || !$instructor) {
                    throw new RuntimeException('Course, section, and instructor are required.');
                }
                if ($enrolled < 0) {
                    throw new RuntimeException('Enrolled count must be non-negative.');
                }
                $stmt = $pdo->prepare('INSERT INTO Section(course_no, year, term, section_no, instructor_id, enrolled_count)
                    VALUES (?,?,?,?,?,?) ON DUPLICATE KEY UPDATE instructor_id=VALUES(instructor_id), enrolled_count=VALUES(enrolled_count)');
                $stmt->execute([$courseNo, (int)$year, $term, $sectionNo, $instructor, $enrolled]);
                $messages[] = 'Section saved.';
                break;
            case 'save_evaluation':
                $courseNo = $_POST['course_no'] ?? '';
                $sectionNo = $_POST['section_no'] ?? '';
                $year = (int)($_POST['year'] ?? 0);
                $term = $_POST['term'] ?? '';
                $degreeName = $_POST['degree_name'] ?? '';
                $degreeLevel = $_POST['degree_level'] ?? '';
                $objective = $_POST['objective_code'] ?? '';
                $method = trim($_POST['method_label'] ?? '');
                $aCount = $_POST['a_count'] !== '' ? (int)$_POST['a_count'] : null;
                $bCount = $_POST['b_count'] !== '' ? (int)$_POST['b_count'] : null;
                $cCount = $_POST['c_count'] !== '' ? (int)$_POST['c_count'] : null;
                $fCount = $_POST['f_count'] !== '' ? (int)$_POST['f_count'] : null;
                $improvement = trim($_POST['improvement_text'] ?? '');
                if (!$courseNo || !$sectionNo || !$year || !$term || !$degreeName || !$degreeLevel || !$objective) {
                    throw new RuntimeException('Missing evaluation identifiers.');
                }
                $sectionStmt = $pdo->prepare('SELECT enrolled_count FROM Section WHERE course_no=? AND year=? AND term=? AND section_no=?');
                $sectionStmt->execute([$courseNo, $year, $term, $sectionNo]);
                $sectionRow = $sectionStmt->fetchColumn();
                if ($sectionRow === false) {
                    throw new RuntimeException('Section not found.');
                }
                $dcoStmt = $pdo->prepare('SELECT 1 FROM DegreeCourseObjective WHERE name=? AND level=? AND course_no=? AND objective_code=?');
                $dcoStmt->execute([$degreeName, $degreeLevel, $courseNo, $objective]);
                if (!$dcoStmt->fetch()) {
                    throw new RuntimeException('Objective is not valid for this degree/course.');
                }
                $counts = array_filter([$aCount, $bCount, $cCount, $fCount], fn($v) => $v !== null);
                if (!empty($counts)) {
                    $totalCounts = array_sum($counts);
                    if ($totalCounts > (int)$sectionRow) {
                        throw new RuntimeException('Counts cannot exceed the enrolled total.');
                    }
                }
                $stmt = $pdo->prepare('INSERT INTO Evaluation(course_no, year, term, section_no, name, level, objective_code,
                        method_label, a_count, b_count, c_count, f_count, improvement_text)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ON DUPLICATE KEY UPDATE method_label=VALUES(method_label), a_count=VALUES(a_count), b_count=VALUES(b_count),
                        c_count=VALUES(c_count), f_count=VALUES(f_count), improvement_text=VALUES(improvement_text)');
                $stmt->execute([
                    $courseNo,
                    $year,
                    $term,
                    $sectionNo,
                    $degreeName,
                    $degreeLevel,
                    $objective,
                    $method ?: null,
                    $aCount,
                    $bCount,
                    $cCount,
                    $fCount,
                    $improvement ?: null,
                ]);
                $messages[] = 'Evaluation saved.';
                break;
            case 'copy_evaluation':
                $courseNo = $_POST['course_no'] ?? '';
                $sectionNo = $_POST['section_no'] ?? '';
                $year = (int)($_POST['year'] ?? 0);
                $term = $_POST['term'] ?? '';
                $degreeName = $_POST['degree_name'] ?? '';
                $degreeLevel = $_POST['degree_level'] ?? '';
                $objective = $_POST['objective_code'] ?? '';
                $target = explode('|', $_POST['target_degree'] ?? '');
                if (count($target) !== 2) {
                    throw new RuntimeException('Select a destination degree.');
                }
                [$targetName, $targetLevel] = $target;
                $selectStmt = $pdo->prepare('SELECT method_label, a_count, b_count, c_count, f_count, improvement_text
                    FROM Evaluation WHERE course_no=? AND year=? AND term=? AND section_no=? AND name=? AND level=? AND objective_code=?');
                $selectStmt->execute([$courseNo, $year, $term, $sectionNo, $degreeName, $degreeLevel, $objective]);
                $sourceRow = $selectStmt->fetch(PDO::FETCH_ASSOC);
                if (!$sourceRow) {
                    throw new RuntimeException('No evaluation exists to copy.');
                }
                $checkStmt = $pdo->prepare('SELECT 1 FROM DegreeCourseObjective WHERE name=? AND level=? AND course_no=? AND objective_code=?');
                $checkStmt->execute([$targetName, $targetLevel, $courseNo, $objective]);
                if (!$checkStmt->fetch()) {
                    throw new RuntimeException('Destination degree does not own this objective.');
                }
                $insert = $pdo->prepare('INSERT INTO Evaluation(course_no, year, term, section_no, name, level, objective_code,
                        method_label, a_count, b_count, c_count, f_count, improvement_text)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ON DUPLICATE KEY UPDATE method_label=VALUES(method_label), a_count=VALUES(a_count), b_count=VALUES(b_count),
                        c_count=VALUES(c_count), f_count=VALUES(f_count), improvement_text=VALUES(improvement_text)');
                $insert->execute([
                    $courseNo,
                    $year,
                    $term,
                    $sectionNo,
                    $targetName,
                    $targetLevel,
                    $objective,
                    $sourceRow['method_label'],
                    $sourceRow['a_count'],
                    $sourceRow['b_count'],
                    $sourceRow['c_count'],
                    $sourceRow['f_count'],
                    $sourceRow['improvement_text'],
                ]);
                $messages[] = 'Evaluation copied to the selected degree.';
                break;
            case 'set_dc_selection':
                $key = $_POST['degree_key'] ?? '';
                if ($key && strpos($key, '|') !== false) {
                    [$degName, $degLevel] = explode('|', $key, 2);
                } else {
                    $degName = $_POST['degree_name'] ?? '';
                    $degLevel = $_POST['degree_level'] ?? '';
                }
                $_SESSION['dc_selection'] = [
                    'name' => $degName,
                    'level' => $degLevel,
                ];
                break;
            case 'set_dco_selection':
                $key = $_POST['degree_key'] ?? '';
                if ($key && strpos($key, '|') !== false) {
                    [$degName, $degLevel] = explode('|', $key, 2);
                } else {
                    $degName = $_POST['degree_name'] ?? '';
                    $degLevel = $_POST['degree_level'] ?? '';
                }
                $_SESSION['dco_selection'] = [
                    'name' => $degName,
                    'level' => $degLevel,
                    'course' => $_POST['course_no'] ?? '',
                    'core_only' => isset($_POST['core_only']) ? 1 : 0,
                ];
                break;
            case 'set_eval_filter':
                $key = $_POST['degree_key'] ?? '';
                if ($key && strpos($key, '|') !== false) {
                    [$degName, $degLevel] = explode('|', $key, 2);
                } else {
                    $degName = $_POST['degree_name'] ?? '';
                    $degLevel = $_POST['degree_level'] ?? '';
                }
                $_SESSION['eval_filter'] = [
                    'degree_name' => $degName,
                    'degree_level' => $degLevel,
                    'year' => $_POST['year'] ?? '',
                    'term' => $_POST['term'] ?? '',
                    'instructor' => $_POST['instructor_id'] ?? '',
                ];
                break;
            case 'run_degree_query':
                $dqName = $_POST['dq_name'] ?? '';
                $dqLevel = $_POST['dq_level'] ?? '';
                $dqStart = $_POST['dq_start'] ?? '';
                $dqEnd = $_POST['dq_end'] ?? '';
                $dqObjectives = array_values(array_filter((array)($_POST['dq_objectives'] ?? [])));
                $degreeQueryData = [
                    'filters' => [
                        'name' => $dqName,
                        'level' => $dqLevel,
                        'start' => $dqStart,
                        'end' => $dqEnd,
                        'objectives' => $dqObjectives,
                    ],
                    'courses' => fetch_all('SELECT course_no, title, is_core FROM DegreeCourse JOIN Course USING(course_no) WHERE name=? AND level=? ORDER BY course_no', [$dqName, $dqLevel]),
                    'objectives' => fetch_all('SELECT DISTINCT o.code, o.title FROM DegreeCourseObjective d JOIN Objective o ON o.code=d.objective_code WHERE d.name=? AND d.level=? ORDER BY o.code', [$dqName, $dqLevel]),
                    'sections' => fetch_all('SELECT s.course_no, s.section_no, s.year, s.term FROM Section s JOIN DegreeCourse dc ON dc.course_no=s.course_no AND dc.name=? AND dc.level=? ORDER BY s.year, FIELD(s.term,\'Spring\',\'Summer\',\'Fall\'), s.course_no', [$dqName, $dqLevel]),
                    'objective_courses' => [],
                ];
                if (!empty($dqObjectives)) {
                    $placeholders = implode(',', array_fill(0, count($dqObjectives), '?'));
                    $params = array_merge([$dqName, $dqLevel], $dqObjectives);
                    $degreeQueryData['objective_courses'] = fetch_all(
                        "SELECT DISTINCT course_no, objective_code FROM DegreeCourseObjective WHERE name=? AND level=? AND objective_code IN ({$placeholders}) ORDER BY course_no",
                        $params
                    );
                }
                break;
            case 'run_course_query':
                $courseId = $_POST['cq_course'] ?? '';
                $start = $_POST['cq_start'] ?? '';
                $end = $_POST['cq_end'] ?? '';
                $courseQueryData = [
                    'filters' => ['course' => $courseId, 'start' => $start, 'end' => $end],
                    'rows' => fetch_all('SELECT year, term, section_no, instructor_id FROM Section WHERE course_no=? ORDER BY year, FIELD(term,\'Spring\',\'Summer\',\'Fall\'), section_no', [$courseId]),
                ];
                break;
            case 'run_instructor_query':
                $instr = $_POST['iq_instructor'] ?? '';
                $start = $_POST['iq_start'] ?? '';
                $end = $_POST['iq_end'] ?? '';
                $instructorQueryData = [
                    'filters' => ['instructor' => $instr, 'start' => $start, 'end' => $end],
                    'rows' => fetch_all('SELECT course_no, section_no, year, term FROM Section WHERE instructor_id=? ORDER BY year, FIELD(term,\'Spring\',\'Summer\',\'Fall\'), course_no', [$instr]),
                ];
                break;
            case 'run_eval_status':
                $year = (int)($_POST['es_year'] ?? 0);
                $term = $_POST['es_term'] ?? '';
                $evalStatusData = [
                    'filters' => ['year' => $year, 'term' => $term],
                    'rows' => fetch_all(
                        'WITH eval_rollup AS (
                            SELECT course_no, year, term, section_no,
                                   SUM(CASE WHEN method_label IS NOT NULL AND a_count IS NOT NULL AND b_count IS NOT NULL AND c_count IS NOT NULL AND f_count IS NOT NULL THEN 1 ELSE 0 END) AS complete_rows,
                                   SUM(CASE WHEN method_label IS NULL OR a_count IS NULL OR b_count IS NULL OR c_count IS NULL OR f_count IS NULL THEN 1 ELSE 0 END) AS partial_rows,
                                   SUM(CASE WHEN improvement_text IS NOT NULL AND improvement_text <> \'\' THEN 1 ELSE 0 END) AS improved_rows,
                                   COUNT(*) AS total_rows
                            FROM Evaluation
                            WHERE year=? AND term=?
                            GROUP BY course_no, year, term, section_no)
                        SELECT s.course_no, s.section_no, c.title, COALESCE(er.total_rows,0) AS total_rows,
                               COALESCE(er.complete_rows,0) AS complete_rows, COALESCE(er.partial_rows,0) AS partial_rows,
                               COALESCE(er.improved_rows,0) AS improved_rows
                        FROM Section s
                        JOIN Course c ON c.course_no=s.course_no
                        LEFT JOIN eval_rollup er ON er.course_no=s.course_no AND er.year=s.year AND er.term=s.term AND er.section_no=s.section_no
                        WHERE s.year=? AND s.term=?
                        ORDER BY s.course_no, s.section_no',
                        [$year, $term, $year, $term]
                    ),
                ];
                break;
            case 'run_nonf':
                $year = (int)($_POST['nf_year'] ?? 0);
                $term = $_POST['nf_term'] ?? '';
                $threshold = (float)($_POST['nf_threshold'] ?? 0);
                $nonfData = [
                    'filters' => ['year' => $year, 'term' => $term, 'threshold' => $threshold],
                    'rows' => fetch_all(
                        'WITH totals AS (
                            SELECT course_no, year, term, section_no,
                                   SUM(COALESCE(a_count,0)+COALESCE(b_count,0)+COALESCE(c_count,0)) AS nonf,
                                   SUM(COALESCE(a_count,0)+COALESCE(b_count,0)+COALESCE(c_count,0)+COALESCE(f_count,0)) AS total
                            FROM Evaluation
                            WHERE year=? AND term=?
                            GROUP BY course_no, year, term, section_no)
                         SELECT s.course_no, s.section_no, c.title, t.nonf, t.total, s.enrolled_count
                         FROM totals t
                         JOIN Section s ON s.course_no=t.course_no AND s.year=t.year AND s.term=t.term AND s.section_no=t.section_no
                         JOIN Course c ON c.course_no=s.course_no
                         WHERE t.total > 0 AND (t.nonf / t.total) >= ? AND t.total <= s.enrolled_count
                         ORDER BY s.course_no, s.section_no',
                        [$year, $term, $threshold]
                    ),
                ];
                break;
        }

        if ($isMutation && $pdo->inTransaction()) {
            $pdo->commit();
        }
    }
} catch (Throwable $e) {
    if ($pdo instanceof PDO && $pdo->inTransaction()) {
        $pdo->rollBack();
    }
    $errors[] = $e->getMessage();
}

$degrees = fetch_all('SELECT name, level, description FROM Degree ORDER BY name, level');
$courses = fetch_all('SELECT course_no, title FROM Course ORDER BY course_no');
$instructors = fetch_all('SELECT instructor_id, name FROM Instructor ORDER BY name');
$semesters = fetch_all('SELECT year, term FROM Semester ORDER BY year, FIELD(term,\'Spring\',\'Summer\',\'Fall\')');
$objectives = fetch_all('SELECT code, title FROM Objective ORDER BY code');

if (empty($_SESSION['dc_selection']) && !empty($degrees)) {
    $_SESSION['dc_selection'] = ['name' => $degrees[0]['name'], 'level' => $degrees[0]['level']];
}
$dcSelection = $_SESSION['dc_selection'] ?? ['name' => '', 'level' => ''];

if (empty($_SESSION['dco_selection']) && !empty($degrees)) {
    $_SESSION['dco_selection'] = [
        'name' => $degrees[0]['name'],
        'level' => $degrees[0]['level'],
        'course' => '',
        'core_only' => 0,
    ];
}
$dcoSelection = $_SESSION['dco_selection'] ?? ['name' => '', 'level' => '', 'course' => '', 'core_only' => 0];

if (empty($_SESSION['eval_filter']) && !empty($degrees) && !empty($semesters) && !empty($instructors)) {
    $_SESSION['eval_filter'] = [
        'degree_name' => $degrees[0]['name'],
        'degree_level' => $degrees[0]['level'],
        'year' => (string)$semesters[0]['year'],
        'term' => $semesters[0]['term'],
        'instructor' => $instructors[0]['instructor_id'],
    ];
}
$evalFilter = $_SESSION['eval_filter'] ?? ['degree_name' => '', 'degree_level' => '', 'year' => '', 'term' => '', 'instructor' => ''];

$degreeCourseView = [];
if ($dcSelection['name'] && $dcSelection['level']) {
    $degreeCourseView = fetch_all(
        'SELECT c.course_no, c.title, COALESCE(dc.is_core, 0) AS is_core, CASE WHEN dc.course_no IS NULL THEN 0 ELSE 1 END AS linked
         FROM Course c
         LEFT JOIN DegreeCourse dc ON dc.course_no=c.course_no AND dc.name=? AND dc.level=?
         ORDER BY c.course_no',
        [$dcSelection['name'], $dcSelection['level']]
    );
}

$dcoCourses = [];
if ($dcoSelection['name'] && $dcoSelection['level']) {
    $dcoCourses = fetch_all(
        'SELECT course_no, is_core FROM DegreeCourse WHERE name=? AND level=?' . ($dcoSelection['core_only'] ? ' AND is_core=1' : '') . ' ORDER BY course_no',
        [$dcoSelection['name'], $dcoSelection['level']]
    );
    if (!$dcoSelection['course'] && !empty($dcoCourses)) {
        $dcoSelection['course'] = $dcoCourses[0]['course_no'];
    }
}

$dcoRows = [];
if ($dcoSelection['course']) {
    $dcoRows = fetch_all(
        'SELECT d.objective_code, o.title FROM DegreeCourseObjective d JOIN Objective o ON o.code=d.objective_code WHERE d.name=? AND d.level=? AND d.course_no=? ORDER BY d.objective_code',
        [$dcoSelection['name'], $dcoSelection['level'], $dcoSelection['course']]
    );
}

$evaluationRows = [];
if ($evalFilter['degree_name'] && $evalFilter['degree_level'] && $evalFilter['year'] && $evalFilter['term'] && $evalFilter['instructor']) {
    $evaluationRows = fetch_all(
        'SELECT s.course_no, s.section_no, s.year, s.term, s.enrolled_count, c.title,
                o.code AS objective_code, o.title AS objective_title,
                e.method_label, e.a_count, e.b_count, e.c_count, e.f_count, e.improvement_text
         FROM Section s
         JOIN Course c ON c.course_no=s.course_no
         JOIN DegreeCourse dc ON dc.course_no=s.course_no AND dc.name=? AND dc.level=?
         JOIN DegreeCourseObjective dco ON dco.name=dc.name AND dco.level=dc.level AND dco.course_no=dc.course_no
         JOIN Objective o ON o.code=dco.objective_code
         LEFT JOIN Evaluation e ON e.course_no=s.course_no AND e.year=s.year AND e.term=s.term AND e.section_no=s.section_no
            AND e.name=dco.name AND e.level=dco.level AND e.objective_code=dco.objective_code
         WHERE s.year=? AND s.term=? AND s.instructor_id=?
         ORDER BY s.course_no, s.section_no, o.code',
        [$evalFilter['degree_name'], $evalFilter['degree_level'], $evalFilter['year'], $evalFilter['term'], $evalFilter['instructor']]
    );
}

$degreeQueryFilters = $degreeQueryData['filters'] ?? [];
$courseQueryFilters = $courseQueryData['filters'] ?? [];
$instructorQueryFilters = $instructorQueryData['filters'] ?? [];
$evalStatusFilters = $evalStatusData['filters'] ?? [];
$nonfFilters = $nonfData['filters'] ?? [];

function evaluation_status_label(array $row): string
{
    $hasRow = array_filter([
        $row['method_label'],
        $row['a_count'],
        $row['b_count'],
        $row['c_count'],
        $row['f_count'],
    ], fn($v) => $v !== null && $v !== '');
    if (empty($hasRow)) {
        return 'No Evaluation';
    }
    $complete = $row['method_label'] !== null && $row['a_count'] !== null && $row['b_count'] !== null && $row['c_count'] !== null && $row['f_count'] !== null;
    return $complete ? 'Complete' : 'Partial';
}

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Curriculum Assessment Portal</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; background-color: #f8f9fb; }
        header { background: #003366; color: #fff; padding: 1rem 2rem; }
        h1 { margin: 0; font-size: 1.75rem; }
        main { padding: 1.5rem; }
        section { background: #fff; margin-bottom: 1.5rem; padding: 1rem 1.25rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        h2 { margin-top: 0; border-bottom: 2px solid #eee; padding-bottom: 0.5rem; }
        form { margin-bottom: 1rem; }
        label { display: block; margin-bottom: 0.35rem; font-weight: 600; }
        input[type="text"], input[type="number"], select, textarea { width: 100%; padding: 0.45rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        textarea { min-height: 70px; }
        button { background: #0069d9; color: #fff; border: none; border-radius: 4px; padding: 0.45rem 0.85rem; cursor: pointer; }
        button.secondary { background: #999; }
        table { border-collapse: collapse; width: 100%; margin-top: 0.5rem; }
        th, td { border: 1px solid #ddd; padding: 0.4rem; text-align: left; }
        th { background: #f0f2f5; }
        .messages { padding: 0.5rem 1rem; border-radius: 4px; margin-bottom: 1rem; }
        .messages.success { background: #e1f3e6; color: #155724; }
        .messages.error { background: #fdecee; color: #8a1c1c; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; }
        .flex { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }
        .status-label { font-weight: 700; }
    </style>
</head>
<body>
    <header>
        <h1>Curriculum Assessment Portal</h1>
        <p>Manage master data, assignments, sections, and evaluation workflows.</p>
    </header>
    <main>
        <?php if ($messages): ?>
            <div class="messages success">
                <?php foreach ($messages as $msg): ?>
                    <div><?= h($msg) ?></div>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>
        <?php if ($errors): ?>
            <div class="messages error">
                <?php foreach ($errors as $err): ?>
                    <div><?= h($err) ?></div>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>

        <section id="master-data">
            <h2>Phase 2 — Master Data</h2>
            <p>Use these forms to maintain the reference data that everything else references.</p>
            <div class="grid">
                <div>
                    <h3>Degrees</h3>
                    <form method="post">
                        <input type="hidden" name="action" value="save_degree">
                        <label>Degree Name
                            <input type="text" name="degree_name" placeholder="Computer Science" required>
                        </label>
                        <label>Level
                            <input type="text" name="degree_level" placeholder="Bachelors" required>
                        </label>
                        <label>Description
                            <textarea name="degree_description" placeholder="Short summary"></textarea>
                        </label>
                        <button type="submit">Save / Update Degree</button>
                    </form>
                    <table>
                        <tr><th>Name</th><th>Level</th><th>Description</th><th></th></tr>
                        <?php foreach ($degrees as $deg): ?>
                            <tr>
                                <td><?= h($deg['name']) ?></td>
                                <td><?= h($deg['level']) ?></td>
                                <td><?= h($deg['description']) ?></td>
                                <td>
                                    <form method="post" onsubmit="return confirm('Delete this degree?');">
                                        <input type="hidden" name="action" value="delete_degree">
                                        <input type="hidden" name="degree_name" value="<?= h($deg['name']) ?>">
                                        <input type="hidden" name="degree_level" value="<?= h($deg['level']) ?>">
                                        <button type="submit" class="secondary">Delete</button>
                                    </form>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    </table>
                </div>
                <div>
                    <h3>Courses</h3>
                    <form method="post">
                        <input type="hidden" name="action" value="save_course">
                        <label>Course Number
                            <input type="text" name="course_no" placeholder="CS101" required>
                        </label>
                        <label>Title
                            <input type="text" name="course_title" placeholder="Intro to Programming" required>
                        </label>
                        <label>Description
                            <textarea name="course_description"></textarea>
                        </label>
                        <button type="submit">Save / Update Course</button>
                    </form>
                    <table>
                        <tr><th>Course</th><th>Title</th><th></th></tr>
                        <?php foreach ($courses as $course): ?>
                            <tr>
                                <td><?= h($course['course_no']) ?></td>
                                <td><?= h($course['title']) ?></td>
                                <td>
                                    <form method="post" onsubmit="return confirm('Delete this course?');">
                                        <input type="hidden" name="action" value="delete_course">
                                        <input type="hidden" name="course_no" value="<?= h($course['course_no']) ?>">
                                        <button type="submit" class="secondary">Delete</button>
                                    </form>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    </table>
                </div>
                <div>
                    <h3>Instructors</h3>
                    <form method="post">
                        <input type="hidden" name="action" value="save_instructor">
                        <label>Instructor ID
                            <input type="text" name="instructor_id" placeholder="I001" required>
                        </label>
                        <label>Name
                            <input type="text" name="instructor_name" placeholder="Dr. Ada Byron" required>
                        </label>
                        <button type="submit">Save / Update Instructor</button>
                    </form>
                    <table>
                        <tr><th>ID</th><th>Name</th><th></th></tr>
                        <?php foreach ($instructors as $inst): ?>
                            <tr>
                                <td><?= h($inst['instructor_id']) ?></td>
                                <td><?= h($inst['name']) ?></td>
                                <td>
                                    <form method="post" onsubmit="return confirm('Delete this instructor?');">
                                        <input type="hidden" name="action" value="delete_instructor">
                                        <input type="hidden" name="instructor_id" value="<?= h($inst['instructor_id']) ?>">
                                        <button type="submit" class="secondary">Delete</button>
                                    </form>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    </table>
                </div>
                <div>
                    <h3>Semesters</h3>
                    <form method="post">
                        <input type="hidden" name="action" value="save_semester">
                        <label>Year
                            <input type="number" name="semester_year" placeholder="2024" required>
                        </label>
                        <label>Term
                            <select name="semester_term">
                                <?php foreach ($TERM_OPTIONS as $term): ?>
                                    <option value="<?= h($term) ?>"><?= h($term) ?></option>
                                <?php endforeach; ?>
                            </select>
                        </label>
                        <button type="submit">Save / Update Semester</button>
                    </form>
                    <table>
                        <tr><th>Year</th><th>Term</th><th></th></tr>
                        <?php foreach ($semesters as $sem): ?>
                            <tr>
                                <td><?= h($sem['year']) ?></td>
                                <td><?= h($sem['term']) ?></td>
                                <td>
                                    <form method="post" onsubmit="return confirm('Delete this semester?');">
                                        <input type="hidden" name="action" value="delete_semester">
                                        <input type="hidden" name="semester_year" value="<?= h($sem['year']) ?>">
                                        <input type="hidden" name="semester_term" value="<?= h($sem['term']) ?>">
                                        <button type="submit" class="secondary">Delete</button>
                                    </form>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    </table>
                </div>
                <div>
                    <h3>Objectives</h3>
                    <form method="post">
                        <input type="hidden" name="action" value="save_objective">
                        <label>Code
                            <input type="text" name="objective_code" placeholder="OBJ1" required>
                        </label>
                        <label>Title
                            <input type="text" name="objective_title" placeholder="Problem Solving" required>
                        </label>
                        <label>Description
                            <textarea name="objective_description"></textarea>
                        </label>
                        <button type="submit">Save / Update Objective</button>
                    </form>
                    <table>
                        <tr><th>Code</th><th>Title</th><th></th></tr>
                        <?php foreach ($objectives as $obj): ?>
                            <tr>
                                <td><?= h($obj['code']) ?></td>
                                <td><?= h($obj['title']) ?></td>
                                <td>
                                    <form method="post" onsubmit="return confirm('Delete this objective?');">
                                        <input type="hidden" name="action" value="delete_objective">
                                        <input type="hidden" name="objective_code" value="<?= h($obj['code']) ?>">
                                        <button type="submit" class="secondary">Delete</button>
                                    </form>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    </table>
                </div>
            </div>
        </section>

        <section id="degree-course">
            <h2>Degree – Course Assignment</h2>
            <p>Select a degree to view all courses, toggle core status, and remove associations.</p>
            <form method="post" class="flex">
                <input type="hidden" name="action" value="set_dc_selection">
                <label>Degree
                    <select name="degree_key">
                        <?php foreach ($degrees as $deg): ?>
                            <?php $key = $deg['name'] . '|' . $deg['level']; ?>
                            <option value="<?= h($key) ?>" <?= ($dcSelection['name'] === $deg['name'] && $dcSelection['level'] === $deg['level']) ? 'selected' : '' ?>><?= h($deg['name'] . ' (' . $deg['level'] . ')') ?></option>
                        <?php endforeach; ?>
                    </select>
                </label>
                <button type="submit">Load Courses</button>
            </form>
            <?php if ($dcSelection['name']): ?>
                <table>
                    <tr><th>Course</th><th>Title</th><th>Core?</th><th>Actions</th></tr>
                    <?php foreach ($degreeCourseView as $row): ?>
                        <tr>
                            <td><?= h($row['course_no']) ?></td>
                            <td><?= h($row['title']) ?></td>
                            <td><?= $row['linked'] ? ($row['is_core'] ? 'Core' : 'Elective') : 'Not Linked' ?></td>
                            <td>
                                <form method="post" class="flex">
                                    <input type="hidden" name="action" value="assign_degree_course">
                                    <input type="hidden" name="degree_name" value="<?= h($dcSelection['name']) ?>">
                                    <input type="hidden" name="degree_level" value="<?= h($dcSelection['level']) ?>">
                                    <input type="hidden" name="course_no" value="<?= h($row['course_no']) ?>">
                                    <label><input type="checkbox" name="is_core" value="1" <?= $row['linked'] && $row['is_core'] ? 'checked' : '' ?>> Core</label>
                                    <button type="submit"><?= $row['linked'] ? 'Update' : 'Add' ?></button>
                                </form>
                                <?php if ($row['linked']): ?>
                                    <form method="post" onsubmit="return confirm('Remove this course from the degree?');">
                                        <input type="hidden" name="action" value="remove_degree_course">
                                        <input type="hidden" name="degree_name" value="<?= h($dcSelection['name']) ?>">
                                        <input type="hidden" name="degree_level" value="<?= h($dcSelection['level']) ?>">
                                        <input type="hidden" name="course_no" value="<?= h($row['course_no']) ?>">
                                        <button type="submit" class="secondary">Remove</button>
                                    </form>
                                <?php endif; ?>
                            </td>
                        </tr>
                    <?php endforeach; ?>
                </table>
            <?php endif; ?>
        </section>

        <section id="degree-course-objective">
            <h2>Degree – Course – Objective Assignment</h2>
            <p>Select a degree, optionally limit to core courses, and manage the objectives tied to each course.</p>
            <form method="post" class="flex">
                <input type="hidden" name="action" value="set_dco_selection">
                <label>Degree
                    <select name="degree_key">
                        <?php foreach ($degrees as $deg): ?>
                            <?php $key = $deg['name'] . '|' . $deg['level']; ?>
                            <option value="<?= h($key) ?>" <?= ($dcoSelection['name'] === $deg['name'] && $dcoSelection['level'] === $deg['level']) ? 'selected' : '' ?>><?= h($deg['name'] . ' (' . $deg['level'] . ')') ?></option>
                        <?php endforeach; ?>
                    </select>
                </label>
                <label><input type="checkbox" name="core_only" value="1" <?= $dcoSelection['core_only'] ? 'checked' : '' ?>> Core courses only</label>
                <label>Course
                    <select name="course_no">
                        <?php foreach ($dcoCourses as $course): ?>
                            <option value="<?= h($course['course_no']) ?>" <?= ($dcoSelection['course'] === $course['course_no']) ? 'selected' : '' ?>><?= h($course['course_no']) ?> <?= $course['is_core'] ? '(Core)' : '' ?></option>
                        <?php endforeach; ?>
                    </select>
                </label>
                <button type="submit">Filter</button>
            </form>
            <?php if ($dcoSelection['course']): ?>
                <div class="grid">
                    <div>
                        <h3>Add Objective to <?= h($dcoSelection['course']) ?></h3>
                        <form method="post">
                            <input type="hidden" name="action" value="assign_dco">
                            <input type="hidden" name="degree_name" value="<?= h($dcoSelection['name']) ?>">
                            <input type="hidden" name="degree_level" value="<?= h($dcoSelection['level']) ?>">
                            <input type="hidden" name="course_no" value="<?= h($dcoSelection['course']) ?>">
                            <label>Objective
                                <select name="objective_code">
                                    <?php foreach ($objectives as $obj): ?>
                                        <option value="<?= h($obj['code']) ?>"><?= h($obj['code'] . ' – ' . $obj['title']) ?></option>
                                    <?php endforeach; ?>
                                </select>
                            </label>
                            <button type="submit">Link Objective</button>
                        </form>
                    </div>
                    <div>
                        <h3>Current Objectives</h3>
                        <table>
                            <tr><th>Code</th><th>Title</th><th></th></tr>
                            <?php foreach ($dcoRows as $row): ?>
                                <tr>
                                    <td><?= h($row['objective_code']) ?></td>
                                    <td><?= h($row['title']) ?></td>
                                    <td>
                                        <form method="post" onsubmit="return confirm('Remove this objective from the course?');">
                                            <input type="hidden" name="action" value="remove_dco">
                                            <input type="hidden" name="degree_name" value="<?= h($dcoSelection['name']) ?>">
                                            <input type="hidden" name="degree_level" value="<?= h($dcoSelection['level']) ?>">
                                            <input type="hidden" name="course_no" value="<?= h($dcoSelection['course']) ?>">
                                            <input type="hidden" name="objective_code" value="<?= h($row['objective_code']) ?>">
                                            <button type="submit" class="secondary">Remove</button>
                                        </form>
                                    </td>
                                </tr>
                            <?php endforeach; ?>
                        </table>
                    </div>
                </div>
            <?php endif; ?>
        </section>

        <section id="section-entry">
            <h2>Section Entry</h2>
            <p>Create or update sections by semester with dropdowns only.</p>
            <form method="post" class="grid">
                <input type="hidden" name="action" value="add_section">
                <label>Course
                    <select name="section_course">
                        <?php foreach ($courses as $course): ?>
                            <option value="<?= h($course['course_no']) ?>"><?= h($course['course_no'] . ' – ' . $course['title']) ?></option>
                        <?php endforeach; ?>
                    </select>
                </label>
                <label>Semester
                    <select name="section_semester">
                        <?php foreach ($semesters as $sem): ?>
                            <option value="<?= h($sem['year'] . '|' . $sem['term']) ?>"><?= h($sem['year'] . ' ' . $sem['term']) ?></option>
                        <?php endforeach; ?>
                    </select>
                </label>
                <label>Section Number
                    <input type="text" name="section_no" placeholder="01" required>
                </label>
                <label>Instructor
                    <select name="section_instructor">
                        <?php foreach ($instructors as $inst): ?>
                            <option value="<?= h($inst['instructor_id']) ?>"><?= h($inst['name']) ?></option>
                        <?php endforeach; ?>
                    </select>
                </label>
                <label>Enrolled Count
                    <input type="number" name="section_enrolled" min="0" value="0">
                </label>
                <div style="align-self: end;">
                    <button type="submit">Save Section</button>
                </div>
            </form>
        </section>

        <section id="evaluation">
            <h2>Phase 3 — Evaluation Workflow</h2>
            <p>Follow the instructor workflow verbatim: pick degree + semester + instructor, edit rows, and copy evaluations.</p>
            <form method="post" class="grid">
                <input type="hidden" name="action" value="set_eval_filter">
                <label>Degree
                    <select name="degree_key">
                        <?php foreach ($degrees as $deg): ?>
                            <?php $key = $deg['name'] . '|' . $deg['level']; ?>
                            <option value="<?= h($key) ?>" <?= ($evalFilter['degree_name'] === $deg['name'] && $evalFilter['degree_level'] === $deg['level']) ? 'selected' : '' ?>><?= h($deg['name'] . ' (' . $deg['level'] . ')') ?></option>
                        <?php endforeach; ?>
                    </select>
                </label>
                <label>Semester
                    <select name="year">
                        <?php foreach ($semesters as $sem): ?>
                            <option value="<?= h($sem['year']) ?>" <?= ($evalFilter['year'] == $sem['year']) ? 'selected' : '' ?>><?= h($sem['year']) ?></option>
                        <?php endforeach; ?>
                    </select>
                    <select name="term">
                        <?php foreach ($TERM_OPTIONS as $term): ?>
                            <option value="<?= h($term) ?>" <?= ($evalFilter['term'] === $term) ? 'selected' : '' ?>><?= h($term) ?></option>
                        <?php endforeach; ?>
                    </select>
                </label>
                <label>Instructor
                    <select name="instructor_id">
                        <?php foreach ($instructors as $inst): ?>
                            <option value="<?= h($inst['instructor_id']) ?>" <?= ($evalFilter['instructor'] === $inst['instructor_id']) ? 'selected' : '' ?>><?= h($inst['name']) ?></option>
                        <?php endforeach; ?>
                    </select>
                </label>
                <div style="align-self: end;">
                    <button type="submit">Load Sections</button>
                </div>
            </form>
            <?php if ($evaluationRows): ?>
                <table>
                    <tr>
                        <th>Section</th><th>Objective</th><th>Status</th><th colspan="2">Evaluation Entry</th><th>Improvement</th><th>Copy To</th>
                    </tr>
                    <?php foreach ($evaluationRows as $row): ?>
                        <?php
                            $status = evaluation_status_label($row);
                            $otherDegrees = fetch_all(
                                'SELECT DISTINCT name, level FROM DegreeCourseObjective WHERE course_no=? AND objective_code=? AND NOT (name=? AND level=?)',
                                [$row['course_no'], $row['objective_code'], $evalFilter['degree_name'], $evalFilter['degree_level']]
                            );
                        ?>
                        <tr>
                            <td>
                                <?= h($row['course_no'] . '-' . $row['section_no']) ?><br>
                                <?= h($row['year'] . ' ' . $row['term']) ?><br>
                                <small><?= h($row['title']) ?> (enrolled <?= h($row['enrolled_count']) ?>)</small>
                            </td>
                            <td><?= h($row['objective_code'] . ' – ' . $row['objective_title']) ?></td>
                            <td class="status-label"><?= h($status) ?></td>
                            <td colspan="2">
                                <form method="post" class="grid">
                                    <input type="hidden" name="action" value="save_evaluation">
                                    <input type="hidden" name="course_no" value="<?= h($row['course_no']) ?>">
                                    <input type="hidden" name="section_no" value="<?= h($row['section_no']) ?>">
                                    <input type="hidden" name="year" value="<?= h($row['year']) ?>">
                                    <input type="hidden" name="term" value="<?= h($row['term']) ?>">
                                    <input type="hidden" name="degree_name" value="<?= h($evalFilter['degree_name']) ?>">
                                    <input type="hidden" name="degree_level" value="<?= h($evalFilter['degree_level']) ?>">
                                    <input type="hidden" name="objective_code" value="<?= h($row['objective_code']) ?>">
                                    <label>Method
                                        <input type="text" name="method_label" value="<?= h($row['method_label']) ?>" placeholder="Exam">
                                    </label>
                                    <label>A Count
                                        <input type="number" name="a_count" min="0" value="<?= h($row['a_count']) ?>">
                                    </label>
                                    <label>B Count
                                        <input type="number" name="b_count" min="0" value="<?= h($row['b_count']) ?>">
                                    </label>
                                    <label>C Count
                                        <input type="number" name="c_count" min="0" value="<?= h($row['c_count']) ?>">
                                    </label>
                                    <label>F Count
                                        <input type="number" name="f_count" min="0" value="<?= h($row['f_count']) ?>">
                                    </label>
                                    <label>Improvement Notes
                                        <textarea name="improvement_text"><?= h($row['improvement_text']) ?></textarea>
                                    </label>
                                    <div style="align-self: end;">
                                        <button type="submit">Save Row</button>
                                    </div>
                                </form>
                            </td>
                            <td><?= $row['improvement_text'] ? 'Yes' : 'No' ?></td>
                            <td>
                                <?php if ($otherDegrees): ?>
                                    <form method="post">
                                        <input type="hidden" name="action" value="copy_evaluation">
                                        <input type="hidden" name="course_no" value="<?= h($row['course_no']) ?>">
                                        <input type="hidden" name="section_no" value="<?= h($row['section_no']) ?>">
                                        <input type="hidden" name="year" value="<?= h($row['year']) ?>">
                                        <input type="hidden" name="term" value="<?= h($row['term']) ?>">
                                        <input type="hidden" name="degree_name" value="<?= h($evalFilter['degree_name']) ?>">
                                        <input type="hidden" name="degree_level" value="<?= h($evalFilter['degree_level']) ?>">
                                        <input type="hidden" name="objective_code" value="<?= h($row['objective_code']) ?>">
                                        <label>Destination
                                            <select name="target_degree">
                                                <?php foreach ($otherDegrees as $deg): ?>
                                                    <?php $key = $deg['name'] . '|' . $deg['level']; ?>
                                                    <option value="<?= h($key) ?>"><?= h($deg['name'] . ' (' . $deg['level'] . ')') ?></option>
                                                <?php endforeach; ?>
                                            </select>
                                        </label>
                                        <button type="submit">Copy</button>
                                    </form>
                                <?php else: ?>
                                    <em>No compatible degrees.</em>
                                <?php endif; ?>
                            </td>
                        </tr>
                    <?php endforeach; ?>
                </table>
            <?php else: ?>
                <p>No sections match the chosen filters.</p>
            <?php endif; ?>
        </section>

        <section id="queries">
            <h2>Phase 4 — Required Queries</h2>
            <div class="grid">
                <div>
                    <h3>Degree Snapshot</h3>
                    <form method="post">
                        <input type="hidden" name="action" value="run_degree_query">
                        <label>Degree
                            <select name="dq_name">
                                <?php foreach ($degrees as $deg): ?>
                                    <option value="<?= h($deg['name']) ?>" <?= ($degreeQueryFilters['name'] ?? '') === $deg['name'] ? 'selected' : '' ?>><?= h($deg['name']) ?></option>
                                <?php endforeach; ?>
                            </select>
                        </label>
                        <label>Level
                            <select name="dq_level">
                                <?php foreach ($degrees as $deg): ?>
                                    <option value="<?= h($deg['level']) ?>" <?= ($degreeQueryFilters['level'] ?? '') === $deg['level'] ? 'selected' : '' ?>><?= h($deg['level']) ?></option>
                                <?php endforeach; ?>
                            </select>
                        </label>
                        <label>Start Semester (e.g., 2023-Fall)
                            <input type="text" name="dq_start" value="<?= h($degreeQueryFilters['start'] ?? '2023-Fall') ?>">
                        </label>
                        <label>End Semester
                            <input type="text" name="dq_end" value="<?= h($degreeQueryFilters['end'] ?? '2024-Fall') ?>">
                        </label>
                        <label>Objectives (hold Ctrl/Cmd for multi-select)
                            <select name="dq_objectives[]" multiple size="4">
                                <?php foreach ($objectives as $obj): ?>
                                    <?php $selected = in_array($obj['code'], $degreeQueryFilters['objectives'] ?? [], true) ? 'selected' : ''; ?>
                                    <option value="<?= h($obj['code']) ?>" <?= $selected ?>><?= h($obj['code'] . ' – ' . $obj['title']) ?></option>
                                <?php endforeach; ?>
                            </select>
                        </label>
                        <button type="submit">Run Degree Query</button>
                    </form>
                    <?php if ($degreeQueryData): ?>
                        <h4>Courses</h4>
                        <ul>
                            <?php foreach ($degreeQueryData['courses'] as $course): ?>
                                <li><?= h($course['course_no'] . ' – ' . $course['title']) ?> (<?= $course['is_core'] ? 'Core' : 'Elective' ?>)</li>
                            <?php endforeach; ?>
                        </ul>
                        <h4>Objectives</h4>
                        <ul>
                            <?php foreach ($degreeQueryData['objectives'] as $obj): ?>
                                <li><?= h($obj['code'] . ': ' . $obj['title']) ?></li>
                            <?php endforeach; ?>
                        </ul>
                        <h4>Sections in Range</h4>
                        <ul>
                            <?php foreach ($degreeQueryData['sections'] as $sec): ?>
                                <?php if (semester_in_range((int)$sec['year'], $sec['term'], $degreeQueryFilters['start'] ?? '1900-Spring', $degreeQueryFilters['end'] ?? '2999-Fall')): ?>
                                    <li><?= h($sec['year'] . ' ' . $sec['term'] . ' ' . $sec['course_no'] . '-' . $sec['section_no']) ?></li>
                                <?php endif; ?>
                            <?php endforeach; ?>
                        </ul>
                        <?php if (!empty($degreeQueryData['objective_courses'])): ?>
                            <h4>Courses by Selected Objectives</h4>
                            <ul>
                                <?php foreach ($degreeQueryData['objective_courses'] as $row): ?>
                                    <li><?= h($row['course_no'] . ' <= ' . $row['objective_code']) ?></li>
                                <?php endforeach; ?>
                            </ul>
                        <?php endif; ?>
                    <?php endif; ?>
                </div>
                <div>
                    <h3>Course Sections</h3>
                    <form method="post">
                        <input type="hidden" name="action" value="run_course_query">
                        <label>Course
                            <select name="cq_course">
                                <?php foreach ($courses as $course): ?>
                                    <option value="<?= h($course['course_no']) ?>" <?= ($courseQueryFilters['course'] ?? '') === $course['course_no'] ? 'selected' : '' ?>><?= h($course['course_no']) ?></option>
                                <?php endforeach; ?>
                            </select>
                        </label>
                        <label>Start Semester
                            <input type="text" name="cq_start" value="<?= h($courseQueryFilters['start'] ?? '2023-Fall') ?>">
                        </label>
                        <label>End Semester
                            <input type="text" name="cq_end" value="<?= h($courseQueryFilters['end'] ?? '2024-Fall') ?>">
                        </label>
                        <button type="submit">List Sections</button>
                    </form>
                    <?php if ($courseQueryData): ?>
                        <ul>
                            <?php foreach ($courseQueryData['rows'] as $row): ?>
                                <?php if (semester_in_range((int)$row['year'], $row['term'], $courseQueryFilters['start'] ?? '1900-Spring', $courseQueryFilters['end'] ?? '2999-Fall')): ?>
                                    <li><?= h($row['year'] . ' ' . $row['term'] . ' section ' . $row['section_no'] . ' instructor ' . $row['instructor_id']) ?></li>
                                <?php endif; ?>
                            <?php endforeach; ?>
                        </ul>
                    <?php endif; ?>
                </div>
                <div>
                    <h3>Instructor Sections</h3>
                    <form method="post">
                        <input type="hidden" name="action" value="run_instructor_query">
                        <label>Instructor
                            <select name="iq_instructor">
                                <?php foreach ($instructors as $inst): ?>
                                    <option value="<?= h($inst['instructor_id']) ?>" <?= ($instructorQueryFilters['instructor'] ?? '') === $inst['instructor_id'] ? 'selected' : '' ?>><?= h($inst['name']) ?></option>
                                <?php endforeach; ?>
                            </select>
                        </label>
                        <label>Start Semester
                            <input type="text" name="iq_start" value="<?= h($instructorQueryFilters['start'] ?? '2023-Fall') ?>">
                        </label>
                        <label>End Semester
                            <input type="text" name="iq_end" value="<?= h($instructorQueryFilters['end'] ?? '2024-Fall') ?>">
                        </label>
                        <button type="submit">List Sections</button>
                    </form>
                    <?php if ($instructorQueryData): ?>
                        <ul>
                            <?php foreach ($instructorQueryData['rows'] as $row): ?>
                                <?php if (semester_in_range((int)$row['year'], $row['term'], $instructorQueryFilters['start'] ?? '1900-Spring', $instructorQueryFilters['end'] ?? '2999-Fall')): ?>
                                    <li><?= h($row['year'] . ' ' . $row['term'] . ' ' . $row['course_no'] . '-' . $row['section_no']) ?></li>
                                <?php endif; ?>
                            <?php endforeach; ?>
                        </ul>
                    <?php endif; ?>
                </div>
                <div>
                    <h3>Evaluation Status by Semester</h3>
                    <form method="post">
                        <input type="hidden" name="action" value="run_eval_status">
                        <label>Year
                            <input type="number" name="es_year" value="<?= h($evalStatusFilters['year'] ?? '2024') ?>">
                        </label>
                        <label>Term
                            <select name="es_term">
                                <?php foreach ($TERM_OPTIONS as $term): ?>
                                    <option value="<?= h($term) ?>" <?= ($evalStatusFilters['term'] ?? '') === $term ? 'selected' : '' ?>><?= h($term) ?></option>
                                <?php endforeach; ?>
                            </select>
                        </label>
                        <button type="submit">Summarize</button>
                    </form>
                    <?php if ($evalStatusData): ?>
                        <ul>
                            <?php foreach ($evalStatusData['rows'] as $row): ?>
                                <?php
                                if ((int)$row['total_rows'] === 0) {
                                    $status = 'No Evaluation';
                                } elseif ((int)$row['partial_rows'] > 0) {
                                    $status = 'Partial';
                                } elseif ((int)$row['complete_rows'] === (int)$row['total_rows']) {
                                    $status = 'Complete';
                                } else {
                                    $status = 'Partial';
                                }
                                $improve = ((int)$row['improved_rows'] > 0) ? 'Yes' : 'No';
                                ?>
                                <li><?= h($row['course_no'] . '-' . $row['section_no'] . ': ' . $status . ' (Improvement: ' . $improve . ')') ?></li>
                            <?php endforeach; ?>
                        </ul>
                    <?php endif; ?>
                </div>
                <div>
                    <h3>Percent Non-F Query</h3>
                    <form method="post">
                        <input type="hidden" name="action" value="run_nonf">
                        <label>Year
                            <input type="number" name="nf_year" value="<?= h($nonfFilters['year'] ?? '2024') ?>">
                        </label>
                        <label>Term
                            <select name="nf_term">
                                <?php foreach ($TERM_OPTIONS as $term): ?>
                                    <option value="<?= h($term) ?>" <?= ($nonfFilters['term'] ?? '') === $term ? 'selected' : '' ?>><?= h($term) ?></option>
                                <?php endforeach; ?>
                            </select>
                        </label>
                        <label>Threshold (0-1)
                            <input type="number" step="0.01" name="nf_threshold" value="<?= h($nonfFilters['threshold'] ?? '0.8') ?>">
                        </label>
                        <button type="submit">Filter Sections</button>
                    </form>
                    <?php if ($nonfData): ?>
                        <ul>
                            <?php foreach ($nonfData['rows'] as $row): ?>
                                <?php $pct = $row['total'] ? round($row['nonf'] / $row['total'], 3) : 0; ?>
                                <li><?= h($row['course_no'] . '-' . $row['section_no'] . ': ' . $row['nonf'] . '/' . $row['total'] . ' (' . $pct . ')') ?></li>
                            <?php endforeach; ?>
                        </ul>
                    <?php endif; ?>
                </div>
            </div>
        </section>
    </main>
</body>
</html>
