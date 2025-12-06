from __future__ import annotations

import os
from typing import Any, Dict, List, Sequence, Tuple

from flask import Flask, flash, g, redirect, render_template, request, url_for

from db import create_connection


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev")

TERM_OPTIONS = ["Spring", "Summer", "Fall"]
LEVEL_OPTIONS = ["BA", "BS", "MS", "Ph.D.", "Cert"]
TERM_ORDER = {"Spring": 1, "Summer": 2, "Fall": 3}
NAV_LINKS = [
    {"endpoint": "home", "label": "Home"},
    {"endpoint": "manage_degrees", "label": "Manage Degrees"},
    {"endpoint": "manage_courses", "label": "Manage Courses"},
    {"endpoint": "manage_objectives", "label": "Manage Objectives"},
    {"endpoint": "manage_semesters", "label": "Manage Semesters & Sections"},
    {"endpoint": "course_objectives", "label": "Associate Courses with Objectives"},
    {"endpoint": "evaluations", "label": "Enter/Review Evaluations"},
    {"endpoint": "reports", "label": "Run Queries / Reports"},
]


def get_db():
    if "db_conn" not in g:
        g.db_conn = create_connection()
    return g.db_conn


@app.teardown_appcontext
def close_db(exception: Exception | None):
    conn = g.pop("db_conn", None)
    if conn is not None:
        conn.close()


def query_all(conn, sql: str, params: Sequence[Any] | None = None) -> List[Dict[str, Any]]:
    with conn.cursor() as cursor:
        cursor.execute(sql, params or ())
        return list(cursor.fetchall())


def query_one(conn, sql: str, params: Sequence[Any] | None = None) -> Dict[str, Any] | None:
    rows = query_all(conn, sql, params)
    return rows[0] if rows else None


def query_scalar(conn, sql: str, params: Sequence[Any] | None = None) -> Any:
    row = query_one(conn, sql, params)
    if not row:
        return None
    return next(iter(row.values()))


def execute(conn, sql: str, params: Sequence[Any] | None = None) -> None:
    with conn.cursor() as cursor:
        cursor.execute(sql, params or ())


def parse_int(value: str | None, default: int | None = None) -> int | None:
    try:
        return int(value) if value is not None and value != "" else default
    except ValueError:
        return default


def semester_value(year: int, term: str) -> int:
    return (int(year) * 10) + TERM_ORDER.get(term, 0)


def parse_degree_key(key: str | None) -> Tuple[str, str] | None:
    if not key or "|" not in key:
        return None
    name, level = key.split("|", 1)
    return name, level


def evaluation_status_label(row: Dict[str, Any]) -> str:
    has_values = [
        row.get("method_label"),
        row.get("a_count"),
        row.get("b_count"),
        row.get("c_count"),
        row.get("f_count"),
    ]
    if not any(v not in (None, "") for v in has_values):
        return "No Evaluation"
    complete = all(row.get(key) is not None for key in ("method_label", "a_count", "b_count", "c_count", "f_count"))
    return "Complete" if complete else "Partial"


def evaluation_complete(row: Dict[str, Any]) -> bool:
    return evaluation_status_label(row) == "Complete"


@app.context_processor
def inject_globals():
    return {
        "term_options": TERM_OPTIONS,
        "level_options": LEVEL_OPTIONS,
        "nav_links": NAV_LINKS,
    }


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/degrees", methods=["GET", "POST"])
def manage_degrees():
    conn = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        next_degree = request.form.get("next_degree") or ""
        next_course = request.form.get("next_course") or ""
        try:
            if action == "create_degree":
                name = (request.form.get("degree_name") or "").strip()
                level = (request.form.get("degree_level") or "").strip()
                description = (request.form.get("degree_description") or "").strip()
                if not name or not level:
                    raise RuntimeError("Degree name and level are required.")
                if level not in LEVEL_OPTIONS:
                    raise RuntimeError("Level must be one of the approved values.")
                execute(
                    conn,
                    "INSERT INTO Degree(name, level, description) VALUES (%s,%s,%s) "
                    "ON DUPLICATE KEY UPDATE description=VALUES(description)",
                    (name, level, description or None),
                )
                next_degree = f"{name}|{level}"
                flash(f"Degree saved for {name} ({level}).", "success")
            elif action == "delete_degree":
                name = (request.form.get("degree_name") or "").strip()
                level = (request.form.get("degree_level") or "").strip()
                if not name or not level:
                    raise RuntimeError("Degree name and level are required.")
                execute(conn, "DELETE FROM Degree WHERE name=%s AND level=%s", (name, level))
                flash(f"Degree {name} ({level}) deleted.", "success")
            elif action == "add_degree_course":
                name = (request.form.get("degree_name") or "").strip()
                level = (request.form.get("degree_level") or "").strip()
                course_no = (request.form.get("course_no") or "").strip()
                is_core = 1 if request.form.get("is_core") else 0
                if not name or not level or not course_no:
                    raise RuntimeError("Degree and course are required.")
                existing = query_scalar(
                    conn,
                    "SELECT is_core FROM DegreeCourse WHERE name=%s AND level=%s AND course_no=%s",
                    (name, level, course_no),
                )
                if existing is not None and int(existing) == 1 and is_core == 0:
                    remaining = query_scalar(
                        conn,
                        "SELECT COUNT(*) FROM DegreeCourse WHERE name=%s AND level=%s AND is_core=1 AND course_no<>%s",
                        (name, level, course_no),
                    )
                    if int(remaining or 0) == 0:
                        raise RuntimeError("Each degree must keep at least one core course.")
                if is_core == 1:
                    obj_count = query_scalar(
                        conn,
                        "SELECT COUNT(*) FROM DegreeCourseObjective WHERE name=%s AND level=%s AND course_no=%s",
                        (name, level, course_no),
                    )
                    if int(obj_count or 0) == 0:
                        raise RuntimeError("Add at least one objective before marking the course as core.")
                execute(
                    conn,
                    "INSERT INTO DegreeCourse(name, level, course_no, is_core) VALUES (%s,%s,%s,%s) "
                    "ON DUPLICATE KEY UPDATE is_core=VALUES(is_core)",
                    (name, level, course_no, is_core),
                )
                next_degree = f"{name}|{level}"
                next_course = course_no
                flash("Degree-course link saved.", "success")
            elif action == "remove_degree_course":
                name = (request.form.get("degree_name") or "").strip()
                level = (request.form.get("degree_level") or "").strip()
                course_no = (request.form.get("course_no") or "").strip()
                if not name or not level or not course_no:
                    raise RuntimeError("Degree and course are required.")
                is_core = query_scalar(
                    conn,
                    "SELECT is_core FROM DegreeCourse WHERE name=%s AND level=%s AND course_no=%s",
                    (name, level, course_no),
                )
                if is_core is not None and int(is_core) == 1:
                    core_count = query_scalar(
                        conn,
                        "SELECT COUNT(*) FROM DegreeCourse WHERE name=%s AND level=%s AND is_core=1",
                        (name, level),
                    )
                    if int(core_count or 0) <= 1:
                        raise RuntimeError("Cannot remove the last core course from a degree.")
                execute(
                    conn,
                    "DELETE FROM DegreeCourse WHERE name=%s AND level=%s AND course_no=%s",
                    (name, level, course_no),
                )
                next_degree = f"{name}|{level}"
                flash("Degree-course link removed.", "success")
            elif action == "add_dco":
                name = (request.form.get("degree_name") or "").strip()
                level = (request.form.get("degree_level") or "").strip()
                course_no = (request.form.get("course_no") or "").strip()
                objective = (request.form.get("objective_code") or "").strip()
                if not name or not level or not course_no or not objective:
                    raise RuntimeError("Complete the degree, course, and objective selection.")
                execute(
                    conn,
                    "INSERT INTO DegreeCourseObjective(name, level, course_no, objective_code) VALUES (%s,%s,%s,%s) "
                    "ON DUPLICATE KEY UPDATE objective_code=objective_code",
                    (name, level, course_no, objective),
                )
                next_degree = f"{name}|{level}"
                next_course = course_no
                flash("Objective linked to course.", "success")
            elif action == "remove_dco":
                name = (request.form.get("degree_name") or "").strip()
                level = (request.form.get("degree_level") or "").strip()
                course_no = (request.form.get("course_no") or "").strip()
                objective = (request.form.get("objective_code") or "").strip()
                if not name or not level or not course_no or not objective:
                    raise RuntimeError("Complete the degree, course, and objective selection.")
                is_core = int(
                    query_scalar(
                        conn,
                        "SELECT is_core FROM DegreeCourse WHERE name=%s AND level=%s AND course_no=%s",
                        (name, level, course_no),
                    )
                    or 0
                )
                if is_core == 1:
                    count_obj = query_scalar(
                        conn,
                        "SELECT COUNT(*) FROM DegreeCourseObjective WHERE name=%s AND level=%s AND course_no=%s",
                        (name, level, course_no),
                    )
                    if int(count_obj or 0) <= 1:
                        raise RuntimeError("Core courses must keep at least one objective.")
                degree_obj_count = query_scalar(
                    conn,
                    "SELECT COUNT(*) FROM DegreeCourseObjective WHERE name=%s AND level=%s AND objective_code=%s AND NOT (course_no=%s AND objective_code=%s)",
                    (name, level, objective, course_no, objective),
                )
                if int(degree_obj_count or 0) == 0:
                    raise RuntimeError("Each objective must remain tied to at least one course for the degree.")
                execute(
                    conn,
                    "DELETE FROM DegreeCourseObjective WHERE name=%s AND level=%s AND course_no=%s AND objective_code=%s",
                    (name, level, course_no, objective),
                )
                next_degree = f"{name}|{level}"
                next_course = course_no
                flash("Objective removed from course.", "success")
        except Exception as exc:
            flash(str(exc), "error")
        query_args = {k: v for k, v in {"degree": next_degree, "course": next_course}.items() if v}
        return redirect(url_for("manage_degrees", **query_args))

    degrees = query_all(conn, "SELECT name, level, description FROM Degree ORDER BY name, level")
    courses = query_all(conn, "SELECT course_no, title FROM Course ORDER BY course_no")
    degree_key = request.args.get("degree")
    selected_degree = parse_degree_key(degree_key)
    if not selected_degree and degrees:
        first = degrees[0]
        selected_degree = (first["name"], first["level"])
        degree_key = f"{first['name']}|{first['level']}"
    degree_courses: List[Dict[str, Any]] = []
    if selected_degree:
        degree_courses = query_all(
            conn,
            "SELECT dc.course_no, c.title, dc.is_core FROM DegreeCourse dc "
            "JOIN Course c ON c.course_no=dc.course_no WHERE dc.name=%s AND dc.level=%s ORDER BY dc.course_no",
            selected_degree,
        )
    course_key = request.args.get("course")
    if not course_key and degree_courses:
        course_key = degree_courses[0]["course_no"]
    dco_rows: List[Dict[str, Any]] = []
    available_objectives: List[Dict[str, Any]] = []
    if selected_degree and course_key:
        dco_rows = query_all(
            conn,
            "SELECT d.objective_code, o.title FROM DegreeCourseObjective d "
            "JOIN Objective o ON o.code=d.objective_code "
            "WHERE d.name=%s AND d.level=%s AND d.course_no=%s ORDER BY d.objective_code",
            (*selected_degree, course_key),
        )
        available_objectives = query_all(
            conn,
            "SELECT code, title FROM Objective WHERE code NOT IN ("
            "SELECT objective_code FROM DegreeCourseObjective WHERE name=%s AND level=%s AND course_no=%s"
            ") ORDER BY code",
            (*selected_degree, course_key),
        )

    return render_template(
        "degrees.html",
        degrees=degrees,
        courses=courses,
        degree_key=degree_key or "",
        course_key=course_key or "",
        selected_degree=selected_degree,
        degree_courses=degree_courses,
        dco_rows=dco_rows,
        available_objectives=available_objectives,
    )


@app.route("/courses", methods=["GET", "POST"])
def manage_courses():
    conn = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "create_course":
                course_no = (request.form.get("course_no") or "").strip()
                title = (request.form.get("course_title") or "").strip()
                description = (request.form.get("course_description") or "").strip()
                if not course_no or not title:
                    raise RuntimeError("Course number and title are required.")
                execute(
                    conn,
                    "INSERT INTO Course(course_no, title, description) VALUES (%s,%s,%s) "
                    "ON DUPLICATE KEY UPDATE title=VALUES(title), description=VALUES(description)",
                    (course_no, title, description or None),
                )
                flash(f"Course {course_no} saved.", "success")
            elif action == "delete_course":
                course_no = (request.form.get("course_no") or "").strip()
                execute(conn, "DELETE FROM Course WHERE course_no=%s", (course_no,))
                flash(f"Course {course_no} deleted.", "success")
            elif action == "create_instructor":
                instructor_id = (request.form.get("instructor_id") or "").strip()
                name = (request.form.get("instructor_name") or "").strip()
                if not instructor_id or not name:
                    raise RuntimeError("Instructor ID and name are required.")
                execute(
                    conn,
                    "INSERT INTO Instructor(instructor_id, name) VALUES (%s,%s) "
                    "ON DUPLICATE KEY UPDATE name=VALUES(name)",
                    (instructor_id, name),
                )
                flash(f"Instructor {instructor_id} saved.", "success")
            elif action == "delete_instructor":
                instructor_id = (request.form.get("instructor_id") or "").strip()
                execute(conn, "DELETE FROM Instructor WHERE instructor_id=%s", (instructor_id,))
                flash(f"Instructor {instructor_id} deleted.", "success")
        except Exception as exc:
            flash(str(exc), "error")
        return redirect(url_for("manage_courses"))

    courses = query_all(conn, "SELECT course_no, title, description FROM Course ORDER BY course_no")
    instructors = query_all(conn, "SELECT instructor_id, name FROM Instructor ORDER BY name")
    return render_template("courses.html", courses=courses, instructors=instructors)


@app.route("/objectives", methods=["GET", "POST"])
def manage_objectives():
    conn = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "create_objective":
                code = (request.form.get("objective_code") or "").strip()
                title = (request.form.get("objective_title") or "").strip()
                description = (request.form.get("objective_description") or "").strip()
                if not code or not title:
                    raise RuntimeError("Objective code and title are required.")
                execute(
                    conn,
                    "INSERT INTO Objective(code, title, description) VALUES (%s,%s,%s) "
                    "ON DUPLICATE KEY UPDATE title=VALUES(title), description=VALUES(description)",
                    (code, title, description or None),
                )
                flash(f"Objective {code} saved.", "success")
            elif action == "delete_objective":
                code = (request.form.get("objective_code") or "").strip()
                execute(conn, "DELETE FROM Objective WHERE code=%s", (code,))
                flash(f"Objective {code} deleted.", "success")
        except Exception as exc:
            flash(str(exc), "error")
        return redirect(url_for("manage_objectives"))

    objectives = query_all(conn, "SELECT code, title, description FROM Objective ORDER BY code")
    return render_template("objectives.html", objectives=objectives)


@app.route("/semesters", methods=["GET", "POST"])
def manage_semesters():
    conn = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "create_semester":
                year = parse_int(request.form.get("semester_year"))
                term = request.form.get("semester_term") or ""
                if not year or term not in TERM_OPTIONS:
                    raise RuntimeError("Semester year and term are required.")
                execute(
                    conn,
                    "INSERT INTO Semester(year, term) VALUES (%s,%s) ON DUPLICATE KEY UPDATE term=VALUES(term)",
                    (year, term),
                )
                flash(f"Semester {year} {term} saved.", "success")
            elif action == "delete_semester":
                year = parse_int(request.form.get("semester_year"))
                term = request.form.get("semester_term") or ""
                execute(conn, "DELETE FROM Semester WHERE year=%s AND term=%s", (year, term))
                flash(f"Semester {year} {term} deleted.", "success")
            elif action == "save_section":
                course_no = request.form.get("section_course") or ""
                year = parse_int(request.form.get("section_year"))
                term = request.form.get("section_term") or ""
                section_no = (request.form.get("section_no") or "").strip()
                instructor = request.form.get("section_instructor") or ""
                enrolled = parse_int(request.form.get("section_enrolled"), 0)
                if not all([course_no, year, term, section_no, instructor]):
                    raise RuntimeError("Course, semester, section, and instructor are required.")
                execute(
                    conn,
                    "INSERT INTO Section(course_no, year, term, section_no, instructor_id, enrolled_count) "
                    "VALUES (%s,%s,%s,%s,%s,%s) "
                    "ON DUPLICATE KEY UPDATE instructor_id=VALUES(instructor_id), enrolled_count=VALUES(enrolled_count)",
                    (course_no, year, term, section_no, instructor, enrolled or 0),
                )
                flash("Section saved.", "success")
            elif action == "delete_section":
                course_no = request.form.get("section_course") or ""
                year = parse_int(request.form.get("section_year"))
                term = request.form.get("section_term") or ""
                section_no = (request.form.get("section_no") or "").strip()
                execute(
                    conn,
                    "DELETE FROM Section WHERE course_no=%s AND year=%s AND term=%s AND section_no=%s",
                    (course_no, year, term, section_no),
                )
                flash("Section deleted.", "success")
        except Exception as exc:
            flash(str(exc), "error")
        return redirect(url_for("manage_semesters"))

    semesters = query_all(conn, "SELECT year, term FROM Semester ORDER BY year, FIELD(term,'Spring','Summer','Fall')")
    courses = query_all(conn, "SELECT course_no, title FROM Course ORDER BY course_no")
    instructors = query_all(conn, "SELECT instructor_id, name FROM Instructor ORDER BY name")
    sections = query_all(
        conn,
        "SELECT s.course_no, c.title, s.year, s.term, s.section_no, i.name AS instructor_name, s.enrolled_count "
        "FROM Section s JOIN Course c ON c.course_no=s.course_no "
        "JOIN Instructor i ON i.instructor_id=s.instructor_id "
        "ORDER BY s.year, FIELD(s.term,'Spring','Summer','Fall'), s.course_no, s.section_no",
    )
    return render_template(
        "semesters.html",
        semesters=semesters,
        courses=courses,
        instructors=instructors,
        sections=sections,
    )


@app.route("/course-objectives", methods=["GET", "POST"])
def course_objectives():
    conn = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        selected_course = request.form.get("selected_course") or ""
        try:
            if action == "add_course_objective":
                course_no = request.form.get("course_no") or ""
                objective = request.form.get("objective_code") or ""
                if not course_no or not objective:
                    raise RuntimeError("Course and objective are required.")
                execute(
                    conn,
                    "INSERT INTO CourseObjective(course_no, objective_code) VALUES (%s,%s) "
                    "ON DUPLICATE KEY UPDATE objective_code=objective_code",
                    (course_no, objective),
                )
                selected_course = course_no
                flash("Objective linked to course.", "success")
            elif action == "remove_course_objective":
                course_no = request.form.get("course_no") or ""
                objective = request.form.get("objective_code") or ""
                execute(
                    conn,
                    "DELETE FROM CourseObjective WHERE course_no=%s AND objective_code=%s",
                    (course_no, objective),
                )
                selected_course = course_no
                flash("Course-objective link removed.", "success")
        except Exception as exc:
            flash(str(exc), "error")
        return redirect(url_for("course_objectives", course=selected_course))

    courses = query_all(conn, "SELECT course_no, title FROM Course ORDER BY course_no")
    selected_course = request.args.get("course") or (courses[0]["course_no"] if courses else "")
    assigned: List[Dict[str, Any]] = []
    available: List[Dict[str, Any]] = []
    if selected_course:
        assigned = query_all(
            conn,
            "SELECT o.code, o.title FROM CourseObjective co JOIN Objective o ON o.code=co.objective_code "
            "WHERE co.course_no=%s ORDER BY o.code",
            (selected_course,),
        )
        available = query_all(
            conn,
            "SELECT code, title FROM Objective WHERE code NOT IN (SELECT objective_code FROM CourseObjective WHERE course_no=%s) ORDER BY code",
            (selected_course,),
        )
    return render_template(
        "course_objectives.html",
        courses=courses,
        selected_course=selected_course,
        assigned=assigned,
        available=available,
    )


def _evaluation_filter_defaults(degrees: List[Dict[str, Any]], instructors: List[Dict[str, Any]], semesters: List[Dict[str, Any]]):
    degree = {"name": "", "level": ""}
    instructor = ""
    semester = {"year": "", "term": ""}
    if degrees:
        degree = {"name": degrees[0]["name"], "level": degrees[0]["level"]}
    if instructors:
        instructor = instructors[0]["instructor_id"]
    if semesters:
        semester = {"year": semesters[0]["year"], "term": semesters[0]["term"]}
    return degree, instructor, semester


@app.route("/evaluations", methods=["GET", "POST"])
def evaluations():
    conn = get_db()
    degrees = query_all(conn, "SELECT name, level FROM Degree ORDER BY name, level")
    instructors = query_all(conn, "SELECT instructor_id, name FROM Instructor ORDER BY name")
    semesters = query_all(conn, "SELECT year, term FROM Semester ORDER BY year, FIELD(term,'Spring','Summer','Fall')")

    default_degree, default_instructor, default_semester = _evaluation_filter_defaults(degrees, instructors, semesters)

    if request.method == "POST":
        action = request.form.get("action")
        if action == "save_evaluation":
            course_no = request.form.get("course_no") or ""
            section_no = request.form.get("section_no") or ""
            year = parse_int(request.form.get("year"))
            term = request.form.get("term") or ""
            degree_name = request.form.get("degree_name") or ""
            degree_level = request.form.get("degree_level") or ""
            objective = request.form.get("objective_code") or ""
            method = (request.form.get("method_label") or "").strip()
            a_count = request.form.get("a_count")
            b_count = request.form.get("b_count")
            c_count = request.form.get("c_count")
            f_count = request.form.get("f_count")
            improvement = (request.form.get("improvement_text") or "").strip()
            try:
                if not all([course_no, section_no, year, term, degree_name, degree_level, objective]):
                    raise RuntimeError("Missing evaluation identifiers.")
                section_row = query_scalar(
                    conn,
                    "SELECT enrolled_count FROM Section WHERE course_no=%s AND year=%s AND term=%s AND section_no=%s",
                    (course_no, year, term, section_no),
                )
                if section_row is None:
                    raise RuntimeError("Section not found.")
                dco_exists = query_one(
                    conn,
                    "SELECT 1 FROM DegreeCourseObjective WHERE name=%s AND level=%s AND course_no=%s AND objective_code=%s",
                    (degree_name, degree_level, course_no, objective),
                )
                if not dco_exists:
                    raise RuntimeError("Objective is not valid for this degree/course.")
                counts = []
                parsed_counts = []
                for value in (a_count, b_count, c_count, f_count):
                    if value in (None, ""):
                        parsed_counts.append(None)
                    else:
                        parsed_counts.append(int(value))
                counts = [c for c in parsed_counts if c is not None]
                if counts:
                    total_counts = sum(counts)
                    if total_counts > int(section_row):
                        raise RuntimeError("Counts cannot exceed the enrolled total.")
                execute(
                    conn,
                    "INSERT INTO Evaluation(course_no, year, term, section_no, name, level, objective_code, "
                    "method_label, a_count, b_count, c_count, f_count, improvement_text) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                    "ON DUPLICATE KEY UPDATE method_label=VALUES(method_label), a_count=VALUES(a_count), "
                    "b_count=VALUES(b_count), c_count=VALUES(c_count), f_count=VALUES(f_count), "
                    "improvement_text=VALUES(improvement_text)",
                    (
                        course_no,
                        year,
                        term,
                        section_no,
                        degree_name,
                        degree_level,
                        objective,
                        method or None,
                        parsed_counts[0],
                        parsed_counts[1],
                        parsed_counts[2],
                        parsed_counts[3],
                        improvement or None,
                    ),
                )
                flash("Evaluation saved.", "success")
            except Exception as exc:
                flash(str(exc), "error")
            degree_combo = f"{degree_name}|{degree_level}" if degree_name and degree_level else ""
            redirect_params = {
                "degree": degree_combo,
                "degree_name": request.form.get("filter_degree_name") or degree_name,
                "degree_level": request.form.get("filter_degree_level") or degree_level,
                "year": request.form.get("filter_year") or (year or ""),
                "term": request.form.get("filter_term") or term,
                "instructor_id": request.form.get("filter_instructor") or request.form.get("instructor_id") or "",
            }
            return redirect(url_for("evaluations", **{k: v for k, v in redirect_params.items() if v}))

    degree_param = request.args.get("degree")
    degree_tuple = parse_degree_key(degree_param) if degree_param else None
    filter_name = degree_tuple[0] if degree_tuple else (request.args.get("degree_name") or default_degree["name"])
    filter_level = degree_tuple[1] if degree_tuple else (request.args.get("degree_level") or default_degree["level"])
    filter_year = parse_int(request.args.get("year"), default_semester["year"] if semesters else None)
    filter_term = request.args.get("term") or (default_semester["term"] if semesters else "")
    filter_instructor = request.args.get("instructor_id") or default_instructor

    section_rows: List[Dict[str, Any]] = []
    sections_grouped: List[Dict[str, Any]] = []
    if all([filter_name, filter_level, filter_year, filter_term, filter_instructor]):
        section_rows = query_all(
            conn,
            "SELECT s.course_no, c.title, s.section_no, s.year, s.term, s.enrolled_count, "
            "       i.name AS instructor_name, o.code AS objective_code, o.title AS objective_title, "
            "       e.method_label, e.a_count, e.b_count, e.c_count, e.f_count, e.improvement_text "
            "FROM DegreeCourse dc "
            "JOIN Section s ON s.course_no=dc.course_no "
            "JOIN Course c ON c.course_no=s.course_no "
            "JOIN Instructor i ON i.instructor_id=s.instructor_id "
            "JOIN DegreeCourseObjective dco ON dco.name=dc.name AND dco.level=dc.level AND dco.course_no=dc.course_no "
            "JOIN Objective o ON o.code=dco.objective_code "
            "LEFT JOIN Evaluation e ON e.course_no=s.course_no AND e.year=s.year AND e.term=s.term AND e.section_no=s.section_no "
            "    AND e.name=dco.name AND e.level=dco.level AND e.objective_code=dco.objective_code "
            "WHERE dc.name=%s AND dc.level=%s AND s.year=%s AND s.term=%s AND s.instructor_id=%s "
            "ORDER BY s.course_no, s.section_no, o.code",
            (filter_name, filter_level, filter_year, filter_term, filter_instructor),
        )
        for row in section_rows:
            row["status"] = evaluation_status_label(row)
        section_map: Dict[Tuple[str, str, int, str], Dict[str, Any]] = {}
        for row in section_rows:
            key = (row["course_no"], row["section_no"], row["year"], row["term"])
            block = section_map.setdefault(
                key,
                {
                    "course_no": row["course_no"],
                    "title": row["title"],
                    "section_no": row["section_no"],
                    "year": row["year"],
                    "term": row["term"],
                    "instructor_name": row["instructor_name"],
                    "enrolled_count": row["enrolled_count"],
                    "rows": [],
                },
            )
            block["rows"].append(row)
        sections_grouped = []
        for block in section_map.values():
            total_obj = len(block["rows"])
            eval_obj = sum(1 for r in block["rows"] if evaluation_complete(r))
            missing = [
                {"code": r["objective_code"], "title": r["objective_title"]}
                for r in block["rows"]
                if not evaluation_complete(r)
            ]
            percent = (eval_obj / total_obj * 100) if total_obj else 0
            block["total_obj"] = total_obj
            block["eval_obj"] = eval_obj
            block["percent"] = percent
            block["missing"] = missing
            sections_grouped.append(block)
        sections_grouped.sort(key=lambda b: (b["year"], TERM_ORDER.get(b["term"], 0), b["course_no"], b["section_no"]))

    filter_state = {
        "degree_name": filter_name,
        "degree_level": filter_level,
        "degree_key": f"{filter_name}|{filter_level}" if filter_name and filter_level else "",
        "year": filter_year,
        "term": filter_term,
        "instructor_id": filter_instructor,
    }

    return render_template(
        "evaluations.html",
        degrees=degrees,
        instructors=instructors,
        semesters=semesters,
        filter_state=filter_state,
        sections=sections_grouped,
    )


def _semester_bounds(start_year: int | None, start_term: str | None, end_year: int | None, end_term: str | None) -> Tuple[int, int]:
    if not all([start_year, start_term, end_year, end_term]):
        raise RuntimeError("Complete the semester range.")
    start_val = semester_value(start_year, start_term)
    end_val = semester_value(end_year, end_term)
    if start_val > end_val:
        raise RuntimeError("Start semester must be before the end semester.")
    return start_val, end_val


@app.route("/reports", methods=["GET", "POST"])
def reports():
    conn = get_db()
    degrees = query_all(conn, "SELECT name, level FROM Degree ORDER BY name, level")
    courses = query_all(conn, "SELECT course_no, title FROM Course ORDER BY course_no")
    instructors = query_all(conn, "SELECT instructor_id, name FROM Instructor ORDER BY name")
    semesters = query_all(conn, "SELECT year, term FROM Semester ORDER BY year, FIELD(term,'Spring','Summer','Fall')")

    report_data: Dict[str, Any] = {}
    action = request.form.get("action") if request.method == "POST" else None

    def default_semester_bounds():
        if not semesters:
            return (None, None, None, None)
        start = semesters[0]
        end = semesters[-1]
        return (start["year"], start["term"], end["year"], end["term"])

    degree_filters = {
        "degree_name": request.form.get("degree_name") if action == "degree_report" else (degrees[0]["name"] if degrees else ""),
        "degree_level": request.form.get("degree_level") if action == "degree_report" else (degrees[0]["level"] if degrees else ""),
        "start_year": parse_int(request.form.get("start_year")) if action == "degree_report" else (semesters[0]["year"] if semesters else None),
        "start_term": request.form.get("start_term") if action == "degree_report" else (semesters[0]["term"] if semesters else ""),
        "end_year": parse_int(request.form.get("end_year")) if action == "degree_report" else (semesters[-1]["year"] if semesters else None),
        "end_term": request.form.get("end_term") if action == "degree_report" else (semesters[-1]["term"] if semesters else ""),
        "objectives": request.form.getlist("objective_codes") if action == "degree_report" else [],
    }

    course_filters = {
        "course_no": request.form.get("course_no") if action == "course_report" else (courses[0]["course_no"] if courses else ""),
        "start_year": parse_int(request.form.get("course_start_year")) if action == "course_report" else (semesters[0]["year"] if semesters else None),
        "start_term": request.form.get("course_start_term") if action == "course_report" else (semesters[0]["term"] if semesters else ""),
        "end_year": parse_int(request.form.get("course_end_year")) if action == "course_report" else (semesters[-1]["year"] if semesters else None),
        "end_term": request.form.get("course_end_term") if action == "course_report" else (semesters[-1]["term"] if semesters else ""),
    }

    instructor_filters = {
        "instructor_id": request.form.get("report_instructor") if action == "instructor_report" else (instructors[0]["instructor_id"] if instructors else ""),
        "start_year": parse_int(request.form.get("instructor_start_year")) if action == "instructor_report" else (semesters[0]["year"] if semesters else None),
        "start_term": request.form.get("instructor_start_term") if action == "instructor_report" else (semesters[0]["term"] if semesters else ""),
        "end_year": parse_int(request.form.get("instructor_end_year")) if action == "instructor_report" else (semesters[-1]["year"] if semesters else None),
        "end_term": request.form.get("instructor_end_term") if action == "instructor_report" else (semesters[-1]["term"] if semesters else ""),
    }

    eval_status_filters = {
        "year": parse_int(request.form.get("status_year")) if action == "evaluation_status" else (semesters[0]["year"] if semesters else None),
        "term": request.form.get("status_term") if action == "evaluation_status" else (semesters[0]["term"] if semesters else ""),
    }

    nonf_filters = {
        "year": parse_int(request.form.get("nonf_year")) if action == "nonf_report" else (semesters[0]["year"] if semesters else None),
        "term": request.form.get("nonf_term") if action == "nonf_report" else (semesters[0]["term"] if semesters else ""),
        "threshold": float(request.form.get("threshold") or 0) if action == "nonf_report" else 0.7,
    }

    try:
        if action == "degree_report":
            name = degree_filters["degree_name"]
            level = degree_filters["degree_level"]
            start = degree_filters["start_year"]
            start_term = degree_filters["start_term"]
            end = degree_filters["end_year"]
            end_term = degree_filters["end_term"]
            start_val, end_val = _semester_bounds(start, start_term, end, end_term)
            courses_rows = query_all(
                conn,
                "SELECT dc.course_no, c.title, dc.is_core FROM DegreeCourse dc JOIN Course c ON c.course_no=dc.course_no "
                "WHERE dc.name=%s AND dc.level=%s ORDER BY dc.course_no",
                (name, level),
            )
            sections_rows = query_all(
                conn,
                "SELECT s.course_no, c.title, s.section_no, s.term, s.year, i.name AS instructor_name, s.enrolled_count "
                "FROM DegreeCourse dc JOIN Section s ON s.course_no=dc.course_no "
                "JOIN Course c ON c.course_no=s.course_no JOIN Instructor i ON i.instructor_id=s.instructor_id "
                "WHERE dc.name=%s AND dc.level=%s AND ((s.year*10 + CASE s.term WHEN 'Spring' THEN 1 WHEN 'Summer' THEN 2 WHEN 'Fall' THEN 3 ELSE 0 END) BETWEEN %s AND %s) "
                "ORDER BY s.year, FIELD(s.term,'Spring','Summer','Fall'), s.course_no, s.section_no",
                (name, level, start_val, end_val),
            )
            objectives_rows = query_all(
                conn,
                "SELECT DISTINCT o.code, o.title FROM DegreeCourseObjective d JOIN Objective o ON o.code=d.objective_code "
                "WHERE d.name=%s AND d.level=%s ORDER BY o.code",
                (name, level),
            )
            objective_courses: List[Dict[str, Any]] = []
            if degree_filters["objectives"]:
                placeholders = ",".join(["%s"] * len(degree_filters["objectives"]))
                params: List[Any] = [name, level, *degree_filters["objectives"]]
                objective_courses = query_all(
                    conn,
                    f"SELECT objective_code, course_no FROM DegreeCourseObjective WHERE name=%s AND level=%s AND objective_code IN ({placeholders}) "
                    "ORDER BY objective_code, course_no",
                    params,
                )
            report_data["degree_report"] = {
                "filters": degree_filters,
                "courses": courses_rows,
                "sections": sections_rows,
                "objectives": objectives_rows,
                "objective_courses": objective_courses,
            }
        elif action == "course_report":
            course_no = course_filters["course_no"]
            start = course_filters["start_year"]
            start_term = course_filters["start_term"]
            end = course_filters["end_year"]
            end_term = course_filters["end_term"]
            start_val, end_val = _semester_bounds(start, start_term, end, end_term)
            rows = query_all(
                conn,
                "SELECT s.year, s.term, s.section_no, i.name AS instructor_name, s.enrolled_count "
                "FROM Section s JOIN Instructor i ON i.instructor_id=s.instructor_id "
                "WHERE s.course_no=%s AND ((s.year*10 + CASE s.term WHEN 'Spring' THEN 1 WHEN 'Summer' THEN 2 WHEN 'Fall' THEN 3 ELSE 0 END) BETWEEN %s AND %s) "
                "ORDER BY s.year, FIELD(s.term,'Spring','Summer','Fall'), s.section_no",
                (course_no, start_val, end_val),
            )
            report_data["course_report"] = {"filters": course_filters, "rows": rows}
        elif action == "instructor_report":
            instructor_id = instructor_filters["instructor_id"]
            start = instructor_filters["start_year"]
            start_term = instructor_filters["start_term"]
            end = instructor_filters["end_year"]
            end_term = instructor_filters["end_term"]
            start_val, end_val = _semester_bounds(start, start_term, end, end_term)
            rows = query_all(
                conn,
                "SELECT s.course_no, c.title, s.section_no, s.year, s.term, s.enrolled_count "
                "FROM Section s JOIN Course c ON c.course_no=s.course_no "
                "WHERE s.instructor_id=%s AND ((s.year*10 + CASE s.term WHEN 'Spring' THEN 1 WHEN 'Summer' THEN 2 WHEN 'Fall' THEN 3 ELSE 0 END) BETWEEN %s AND %s) "
                "ORDER BY s.year, FIELD(s.term,'Spring','Summer','Fall'), s.course_no, s.section_no",
                (instructor_id, start_val, end_val),
            )
            report_data["instructor_report"] = {"filters": instructor_filters, "rows": rows}
        elif action == "evaluation_status":
            year = eval_status_filters["year"]
            term = eval_status_filters["term"]
            rows = query_all(
                conn,
                "SELECT s.course_no, c.title, s.section_no, s.year, s.term, i.name AS instructor_name, s.enrolled_count, "
                "       COALESCE(SUM(CASE WHEN e.method_label IS NOT NULL AND e.a_count IS NOT NULL AND e.b_count IS NOT NULL AND e.c_count IS NOT NULL AND e.f_count IS NOT NULL THEN 1 ELSE 0 END),0) AS complete_rows, "
                "       COALESCE(COUNT(e.objective_code),0) AS eval_rows, "
                "       COALESCE(SUM(CASE WHEN e.improvement_text IS NOT NULL AND e.improvement_text <> '' THEN 1 ELSE 0 END),0) AS improvements "
                "FROM Section s JOIN Course c ON c.course_no=s.course_no JOIN Instructor i ON i.instructor_id=s.instructor_id "
                "LEFT JOIN Evaluation e ON e.course_no=s.course_no AND e.section_no=s.section_no AND e.year=s.year AND e.term=s.term "
                "WHERE s.year=%s AND s.term=%s GROUP BY s.course_no, c.title, s.section_no, s.year, s.term, i.name, s.enrolled_count "
                "ORDER BY s.course_no, s.section_no",
                (year, term),
            )
            for row in rows:
                total = int(row["eval_rows"])
                complete = int(row["complete_rows"])
                if total == 0:
                    row["status"] = "None"
                elif complete == total:
                    row["status"] = "Complete"
                else:
                    row["status"] = "Partial"
                row["has_improvement"] = int(row["improvements"]) > 0
            report_data["evaluation_status"] = {"filters": eval_status_filters, "rows": rows}
        elif action == "nonf_report":
            year = nonf_filters["year"]
            term = nonf_filters["term"]
            threshold = nonf_filters["threshold"]
            rows = query_all(
                conn,
                "SELECT s.course_no, c.title, s.section_no, s.year, s.term, i.name AS instructor_name, s.enrolled_count, "
                "       SUM(COALESCE(e.a_count,0)+COALESCE(e.b_count,0)+COALESCE(e.c_count,0)) AS nonf, "
                "       SUM(COALESCE(e.a_count,0)+COALESCE(e.b_count,0)+COALESCE(e.c_count,0)+COALESCE(e.f_count,0)) AS total "
                "FROM Section s JOIN Course c ON c.course_no=s.course_no JOIN Instructor i ON i.instructor_id=s.instructor_id "
                "JOIN Evaluation e ON e.course_no=s.course_no AND e.year=s.year AND e.term=s.term AND e.section_no=s.section_no "
                "WHERE s.year=%s AND s.term=%s GROUP BY s.course_no, c.title, s.section_no, s.year, s.term, i.name, s.enrolled_count "
                "HAVING CASE WHEN total > 0 THEN (nonf / total) ELSE 0 END >= %s "
                "ORDER BY s.course_no, s.section_no",
                (year, term, threshold),
            )
            for row in rows:
                total = row["total"] or 0
                nonf = row["nonf"] or 0
                row["percent"] = (nonf / total * 100) if total else 0
            report_data["nonf_report"] = {"filters": nonf_filters, "rows": rows}
    except Exception as exc:
        flash(str(exc), "error")

    # Objective options for the degree report form
    objective_options: List[Dict[str, Any]] = []
    if degree_filters["degree_name"] and degree_filters["degree_level"]:
        objective_options = query_all(
            conn,
            "SELECT DISTINCT o.code, o.title FROM DegreeCourseObjective d JOIN Objective o ON o.code=d.objective_code "
            "WHERE d.name=%s AND d.level=%s ORDER BY o.code",
            (degree_filters["degree_name"], degree_filters["degree_level"]),
        )

    return render_template(
        "reports.html",
        degrees=degrees,
        courses=courses,
        instructors=instructors,
        semesters=semesters,
        objective_options=objective_options,
        report_data=report_data,
        degree_filters=degree_filters,
        course_filters=course_filters,
        instructor_filters=instructor_filters,
        eval_status_filters=eval_status_filters,
        nonf_filters=nonf_filters,
    )


if __name__ == "__main__":
    app.run(debug=True)
