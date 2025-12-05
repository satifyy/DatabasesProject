from __future__ import annotations

import os
from typing import Any, Dict, Iterable, List, Sequence

from flask import Flask, g, render_template, request, session

from db import create_connection


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev")

TERM_OPTIONS = ["Spring", "Summer", "Fall"]
MUTATION_ACTIONS = {
    "save_degree",
    "delete_degree",
    "save_course",
    "delete_course",
    "save_instructor",
    "delete_instructor",
    "save_semester",
    "delete_semester",
    "save_objective",
    "delete_objective",
    "assign_degree_course",
    "remove_degree_course",
    "assign_dco",
    "remove_dco",
    "add_section",
    "save_evaluation",
    "copy_evaluation",
}


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


def term_order(term: str) -> int:
    return {"Spring": 1, "Summer": 2, "Fall": 3}.get(term, 0)


def parse_semester_label(label: str) -> Dict[str, Any] | None:
    if "-" not in label:
        return None
    year, term = label.split("-", 1)
    try:
        return {"year": int(year), "term": term}
    except ValueError:
        return None


def semester_in_range(year: int, term: str, start_label: str, end_label: str) -> bool:
    start = parse_semester_label(start_label) or {"year": 0, "term": "Spring"}
    end = parse_semester_label(end_label) or {"year": 9999, "term": "Fall"}
    current_val = (year * 10) + term_order(term)
    start_val = (start["year"] * 10) + term_order(start["term"])
    end_val = (end["year"] * 10) + term_order(end["term"])
    return start_val <= current_val <= end_val


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


app.jinja_env.globals["semester_in_range"] = semester_in_range
app.jinja_env.globals["term_options"] = TERM_OPTIONS
app.jinja_env.globals["evaluation_status_label"] = evaluation_status_label


@app.route("/", methods=["GET", "POST"])
def index():
    conn = get_db()
    messages: List[str] = []
    errors: List[str] = []
    degree_query_data = None
    course_query_data = None
    instructor_query_data = None
    eval_status_data = None
    nonf_data = None

    action = request.form.get("action", "")
    is_mutation = action in MUTATION_ACTIONS

    if request.method == "POST" and action:
        try:
            if is_mutation:
                conn.begin()

            if action == "save_degree":
                name = (request.form.get("degree_name") or "").strip()
                level = (request.form.get("degree_level") or "").strip()
                description = (request.form.get("degree_description") or "").strip()
                if not name or not level:
                    raise RuntimeError("Degree name and level are required.")
                execute(
                    conn,
                    "INSERT INTO Degree(name, level, description) VALUES (%s,%s,%s) "
                    "ON DUPLICATE KEY UPDATE description=VALUES(description)",
                    (name, level, description or None),
                )
                messages.append(f"Degree saved for {name} ({level}).")
            elif action == "delete_degree":
                name = (request.form.get("degree_name") or "").strip()
                level = (request.form.get("degree_level") or "").strip()
                execute(conn, "DELETE FROM Degree WHERE name=%s AND level=%s", (name, level))
                messages.append(f"Degree {name} ({level}) deleted.")
            elif action == "save_course":
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
                messages.append(f"Course {course_no} saved.")
            elif action == "delete_course":
                course_no = (request.form.get("course_no") or "").strip()
                execute(conn, "DELETE FROM Course WHERE course_no=%s", (course_no,))
                messages.append(f"Course {course_no} deleted.")
            elif action == "save_instructor":
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
                messages.append(f"Instructor {instructor_id} saved.")
            elif action == "delete_instructor":
                instructor_id = (request.form.get("instructor_id") or "").strip()
                execute(conn, "DELETE FROM Instructor WHERE instructor_id=%s", (instructor_id,))
                messages.append(f"Instructor {instructor_id} deleted.")
            elif action == "save_semester":
                year = int(request.form.get("semester_year") or 0)
                term = request.form.get("semester_term") or ""
                if not year or not term:
                    raise RuntimeError("Semester year and term are required.")
                execute(
                    conn,
                    "INSERT INTO Semester(year, term) VALUES (%s,%s) "
                    "ON DUPLICATE KEY UPDATE term=VALUES(term)",
                    (year, term),
                )
                messages.append(f"Semester {year} {term} saved.")
            elif action == "delete_semester":
                year = int(request.form.get("semester_year") or 0)
                term = request.form.get("semester_term") or ""
                execute(conn, "DELETE FROM Semester WHERE year=%s AND term=%s", (year, term))
                messages.append(f"Semester {year} {term} deleted.")
            elif action == "save_objective":
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
                messages.append(f"Objective {code} saved.")
            elif action == "delete_objective":
                code = (request.form.get("objective_code") or "").strip()
                execute(conn, "DELETE FROM Objective WHERE code=%s", (code,))
                messages.append(f"Objective {code} deleted.")
            elif action == "assign_degree_course":
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
                        "SELECT COUNT(*) AS count FROM DegreeCourse WHERE name=%s AND level=%s AND is_core=1 AND course_no<>%s",
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
                messages.append("Degree-course link saved.")
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
                if is_core is None:
                    pass
                else:
                    if int(is_core) == 1:
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
                    messages.append("Degree-course link removed.")
            elif action == "assign_dco":
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
                messages.append("Objective linked to course.")
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
                messages.append("Objective removed from course.")
            elif action == "add_section":
                course_no = request.form.get("section_course") or ""
                semester = (request.form.get("section_semester") or "").split("|")
                if len(semester) != 2:
                    raise RuntimeError("Select a semester.")
                year, term = semester
                section_no = (request.form.get("section_no") or "").strip()
                instructor = request.form.get("section_instructor") or ""
                enrolled = int(request.form.get("section_enrolled") or 0)
                if not course_no or not section_no or not instructor:
                    raise RuntimeError("Course, section, and instructor are required.")
                if enrolled < 0:
                    raise RuntimeError("Enrolled count must be non-negative.")
                execute(
                    conn,
                    "INSERT INTO Section(course_no, year, term, section_no, instructor_id, enrolled_count) "
                    "VALUES (%s,%s,%s,%s,%s,%s) "
                    "ON DUPLICATE KEY UPDATE instructor_id=VALUES(instructor_id), enrolled_count=VALUES(enrolled_count)",
                    (course_no, int(year), term, section_no, instructor, enrolled),
                )
                messages.append("Section saved.")
            elif action == "save_evaluation":
                course_no = request.form.get("course_no") or ""
                section_no = request.form.get("section_no") or ""
                year = int(request.form.get("year") or 0)
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
                counts = [
                    int(a_count) if a_count not in (None, "") else None,
                    int(b_count) if b_count not in (None, "") else None,
                    int(c_count) if c_count not in (None, "") else None,
                    int(f_count) if f_count not in (None, "") else None,
                ]
                provided = [c for c in counts if c is not None]
                if provided:
                    total_counts = sum(provided)
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
                        counts[0],
                        counts[1],
                        counts[2],
                        counts[3],
                        improvement or None,
                    ),
                )
                messages.append("Evaluation saved.")
            elif action == "copy_evaluation":
                course_no = request.form.get("course_no") or ""
                section_no = request.form.get("section_no") or ""
                year = int(request.form.get("year") or 0)
                term = request.form.get("term") or ""
                degree_name = request.form.get("degree_name") or ""
                degree_level = request.form.get("degree_level") or ""
                objective = request.form.get("objective_code") or ""
                target = (request.form.get("target_degree") or "").split("|")
                if len(target) != 2:
                    raise RuntimeError("Select a destination degree.")
                target_name, target_level = target
                source_row = query_one(
                    conn,
                    "SELECT method_label, a_count, b_count, c_count, f_count, improvement_text "
                    "FROM Evaluation WHERE course_no=%s AND year=%s AND term=%s AND section_no=%s "
                    "AND name=%s AND level=%s AND objective_code=%s",
                    (course_no, year, term, section_no, degree_name, degree_level, objective),
                )
                if not source_row:
                    raise RuntimeError("No evaluation exists to copy.")
                valid = query_one(
                    conn,
                    "SELECT 1 FROM DegreeCourseObjective WHERE name=%s AND level=%s AND course_no=%s AND objective_code=%s",
                    (target_name, target_level, course_no, objective),
                )
                if not valid:
                    raise RuntimeError("Destination degree does not own this objective.")
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
                        target_name,
                        target_level,
                        objective,
                        source_row["method_label"],
                        source_row["a_count"],
                        source_row["b_count"],
                        source_row["c_count"],
                        source_row["f_count"],
                        source_row["improvement_text"],
                    ),
                )
                messages.append("Evaluation copied to the selected degree.")
            elif action == "set_dc_selection":
                key = request.form.get("degree_key") or ""
                if "|" in key:
                    deg_name, deg_level = key.split("|", 1)
                else:
                    deg_name = request.form.get("degree_name") or ""
                    deg_level = request.form.get("degree_level") or ""
                session["dc_selection"] = {"name": deg_name, "level": deg_level}
            elif action == "set_dco_selection":
                key = request.form.get("degree_key") or ""
                if "|" in key:
                    deg_name, deg_level = key.split("|", 1)
                else:
                    deg_name = request.form.get("degree_name") or ""
                    deg_level = request.form.get("degree_level") or ""
                session["dco_selection"] = {
                    "name": deg_name,
                    "level": deg_level,
                    "course": request.form.get("course_no") or "",
                    "core_only": 1 if request.form.get("core_only") else 0,
                }
            elif action == "set_eval_filter":
                key = request.form.get("degree_key") or ""
                if "|" in key:
                    deg_name, deg_level = key.split("|", 1)
                else:
                    deg_name = request.form.get("degree_name") or ""
                    deg_level = request.form.get("degree_level") or ""
                session["eval_filter"] = {
                    "degree_name": deg_name,
                    "degree_level": deg_level,
                    "year": request.form.get("year") or "",
                    "term": request.form.get("term") or "",
                    "instructor": request.form.get("instructor_id") or "",
                }
            elif action == "run_degree_query":
                dq_name = request.form.get("dq_name") or ""
                dq_level = request.form.get("dq_level") or ""
                dq_start = request.form.get("dq_start") or ""
                dq_end = request.form.get("dq_end") or ""
                dq_objectives = [code for code in request.form.getlist("dq_objectives[]") if code]
                degree_query_data = {
                    "filters": {
                        "name": dq_name,
                        "level": dq_level,
                        "start": dq_start,
                        "end": dq_end,
                        "objectives": dq_objectives,
                    },
                    "courses": query_all(
                        conn,
                        "SELECT course_no, title, is_core FROM DegreeCourse JOIN Course USING(course_no) "
                        "WHERE name=%s AND level=%s ORDER BY course_no",
                        (dq_name, dq_level),
                    ),
                    "objectives": query_all(
                        conn,
                        "SELECT DISTINCT o.code, o.title FROM DegreeCourseObjective d "
                        "JOIN Objective o ON o.code=d.objective_code "
                        "WHERE d.name=%s AND d.level=%s ORDER BY o.code",
                        (dq_name, dq_level),
                    ),
                    "sections": query_all(
                        conn,
                        "SELECT s.course_no, s.section_no, s.year, s.term FROM Section s "
                        "JOIN DegreeCourse dc ON dc.course_no=s.course_no AND dc.name=%s AND dc.level=%s "
                        "ORDER BY s.year, FIELD(s.term,'Spring','Summer','Fall'), s.course_no",
                        (dq_name, dq_level),
                    ),
                    "objective_courses": [],
                }
                if dq_objectives:
                    placeholders = ",".join(["%s"] * len(dq_objectives))
                    params = [dq_name, dq_level, *dq_objectives]
                    degree_query_data["objective_courses"] = query_all(
                        conn,
                        f"SELECT DISTINCT course_no, objective_code FROM DegreeCourseObjective "
                        f"WHERE name=%s AND level=%s AND objective_code IN ({placeholders}) ORDER BY course_no",
                        params,
                    )
            elif action == "run_course_query":
                course_id = request.form.get("cq_course") or ""
                start = request.form.get("cq_start") or ""
                end = request.form.get("cq_end") or ""
                course_query_data = {
                    "filters": {"course": course_id, "start": start, "end": end},
                    "rows": query_all(
                        conn,
                        "SELECT year, term, section_no, instructor_id FROM Section WHERE course_no=%s "
                        "ORDER BY year, FIELD(term,'Spring','Summer','Fall'), section_no",
                        (course_id,),
                    ),
                }
            elif action == "run_instructor_query":
                instructor = request.form.get("iq_instructor") or ""
                start = request.form.get("iq_start") or ""
                end = request.form.get("iq_end") or ""
                instructor_query_data = {
                    "filters": {"instructor": instructor, "start": start, "end": end},
                    "rows": query_all(
                        conn,
                        "SELECT course_no, section_no, year, term FROM Section WHERE instructor_id=%s "
                        "ORDER BY year, FIELD(term,'Spring','Summer','Fall'), course_no",
                        (instructor,),
                    ),
                }
            elif action == "run_eval_status":
                year = int(request.form.get("es_year") or 0)
                term = request.form.get("es_term") or ""
                eval_status_data = {
                    "filters": {"year": year, "term": term},
                    "rows": query_all(
                        conn,
                        "WITH eval_rollup AS ("
                        "    SELECT course_no, year, term, section_no,"
                        "           SUM(CASE WHEN method_label IS NOT NULL AND a_count IS NOT NULL AND b_count IS NOT NULL "
                        "                    AND c_count IS NOT NULL AND f_count IS NOT NULL THEN 1 ELSE 0 END) AS complete_rows,"
                        "           SUM(CASE WHEN method_label IS NULL OR a_count IS NULL OR b_count IS NULL "
                        "                    OR c_count IS NULL OR f_count IS NULL THEN 1 ELSE 0 END) AS partial_rows,"
                        "           SUM(CASE WHEN improvement_text IS NOT NULL AND improvement_text <> '' THEN 1 ELSE 0 END) AS improved_rows,"
                        "           COUNT(*) AS total_rows "
                        "    FROM Evaluation WHERE year=%s AND term=%s GROUP BY course_no, year, term, section_no)"
                        " SELECT s.course_no, s.section_no, c.title, COALESCE(er.total_rows,0) AS total_rows,"
                        "        COALESCE(er.complete_rows,0) AS complete_rows, COALESCE(er.partial_rows,0) AS partial_rows,"
                        "        COALESCE(er.improved_rows,0) AS improved_rows "
                        " FROM Section s "
                        " JOIN Course c ON c.course_no=s.course_no "
                        " LEFT JOIN eval_rollup er ON er.course_no=s.course_no AND er.year=s.year "
                        "     AND er.term=s.term AND er.section_no=s.section_no "
                        " WHERE s.year=%s AND s.term=%s "
                        " ORDER BY s.course_no, s.section_no",
                        (year, term, year, term),
                    ),
                }
            elif action == "run_nonf":
                year = int(request.form.get("nf_year") or 0)
                term = request.form.get("nf_term") or ""
                threshold = float(request.form.get("nf_threshold") or 0)
                nonf_data = {
                    "filters": {"year": year, "term": term, "threshold": threshold},
                    "rows": query_all(
                        conn,
                        "WITH totals AS ("
                        "    SELECT course_no, year, term, section_no,"
                        "           SUM(COALESCE(a_count,0)+COALESCE(b_count,0)+COALESCE(c_count,0)) AS nonf,"
                        "           SUM(COALESCE(a_count,0)+COALESCE(b_count,0)+COALESCE(c_count,0)+COALESCE(f_count,0)) AS total "
                        "    FROM Evaluation WHERE year=%s AND term=%s GROUP BY course_no, year, term, section_no)"
                        " SELECT s.course_no, s.section_no, c.title, t.nonf, t.total, s.enrolled_count "
                        " FROM totals t "
                        " JOIN Section s ON s.course_no=t.course_no AND s.year=t.year AND s.term=t.term AND s.section_no=t.section_no "
                        " JOIN Course c ON c.course_no=s.course_no "
                        " WHERE t.total > 0 AND (t.nonf / t.total) >= %s AND t.total <= s.enrolled_count "
                        " ORDER BY s.course_no, s.section_no",
                        (year, term, threshold),
                    ),
                }

            if is_mutation:
                conn.commit()
        except Exception as exc:
            if is_mutation:
                try:
                    conn.rollback()
                except Exception:
                    pass
            errors.append(str(exc))
            # Clear transient query data on error to avoid stale results.
            degree_query_data = None
            course_query_data = None
            instructor_query_data = None
            eval_status_data = None
            nonf_data = None

    degrees = query_all(conn, "SELECT name, level, description FROM Degree ORDER BY name, level")
    courses = query_all(conn, "SELECT course_no, title FROM Course ORDER BY course_no")
    instructors = query_all(conn, "SELECT instructor_id, name FROM Instructor ORDER BY name")
    semesters = query_all(conn, "SELECT year, term FROM Semester ORDER BY year, FIELD(term,'Spring','Summer','Fall')")
    objectives = query_all(conn, "SELECT code, title FROM Objective ORDER BY code")

    if not session.get("dc_selection") and degrees:
        session["dc_selection"] = {"name": degrees[0]["name"], "level": degrees[0]["level"]}
    dc_selection = session.get("dc_selection", {"name": "", "level": ""})

    if not session.get("dco_selection") and degrees:
        session["dco_selection"] = {
            "name": degrees[0]["name"],
            "level": degrees[0]["level"],
            "course": "",
            "core_only": 0,
        }
    dco_selection = session.get("dco_selection", {"name": "", "level": "", "course": "", "core_only": 0})

    if not session.get("eval_filter") and degrees and semesters and instructors:
        session["eval_filter"] = {
            "degree_name": degrees[0]["name"],
            "degree_level": degrees[0]["level"],
            "year": str(semesters[0]["year"]),
            "term": semesters[0]["term"],
            "instructor": instructors[0]["instructor_id"],
        }
    eval_filter = session.get(
        "eval_filter", {"degree_name": "", "degree_level": "", "year": "", "term": "", "instructor": ""}
    )

    degree_course_view: List[Dict[str, Any]] = []
    if dc_selection.get("name") and dc_selection.get("level"):
        degree_course_view = query_all(
            conn,
            "SELECT c.course_no, c.title, COALESCE(dc.is_core,0) AS is_core, "
            "CASE WHEN dc.course_no IS NULL THEN 0 ELSE 1 END AS linked "
            "FROM Course c "
            "LEFT JOIN DegreeCourse dc ON dc.course_no=c.course_no AND dc.name=%s AND dc.level=%s "
            "ORDER BY c.course_no",
            (dc_selection["name"], dc_selection["level"]),
        )

    dco_courses: List[Dict[str, Any]] = []
    if dco_selection.get("name") and dco_selection.get("level"):
        course_filter = " AND is_core=1" if dco_selection.get("core_only") else ""
        dco_courses = query_all(
            conn,
            f"SELECT course_no, is_core FROM DegreeCourse WHERE name=%s AND level=%s{course_filter} ORDER BY course_no",
            (dco_selection["name"], dco_selection["level"]),
        )
        if not dco_selection.get("course") and dco_courses:
            dco_selection["course"] = dco_courses[0]["course_no"]
            session["dco_selection"] = dco_selection

    dco_rows: List[Dict[str, Any]] = []
    if dco_selection.get("course"):
        dco_rows = query_all(
            conn,
            "SELECT d.objective_code, o.title FROM DegreeCourseObjective d "
            "JOIN Objective o ON o.code=d.objective_code "
            "WHERE d.name=%s AND d.level=%s AND d.course_no=%s ORDER BY d.objective_code",
            (dco_selection["name"], dco_selection["level"], dco_selection["course"]),
        )

    evaluation_rows: List[Dict[str, Any]] = []
    if all(
        [
            eval_filter.get("degree_name"),
            eval_filter.get("degree_level"),
            eval_filter.get("year"),
            eval_filter.get("term"),
            eval_filter.get("instructor"),
        ]
    ):
        evaluation_rows = query_all(
            conn,
            "SELECT s.course_no, s.section_no, s.year, s.term, s.enrolled_count, c.title,"
            "       o.code AS objective_code, o.title AS objective_title,"
            "       e.method_label, e.a_count, e.b_count, e.c_count, e.f_count, e.improvement_text "
            "FROM Section s "
            "JOIN Course c ON c.course_no=s.course_no "
            "JOIN DegreeCourse dc ON dc.course_no=s.course_no AND dc.name=%s AND dc.level=%s "
            "JOIN DegreeCourseObjective dco ON dco.name=dc.name AND dco.level=dc.level AND dco.course_no=dc.course_no "
            "JOIN Objective o ON o.code=dco.objective_code "
            "LEFT JOIN Evaluation e ON e.course_no=s.course_no AND e.year=s.year AND e.term=s.term "
            "    AND e.section_no=s.section_no AND e.name=dco.name AND e.level=dco.level AND e.objective_code=dco.objective_code "
            "WHERE s.year=%s AND s.term=%s AND s.instructor_id=%s "
            "ORDER BY s.course_no, s.section_no, o.code",
            (
                eval_filter["degree_name"],
                eval_filter["degree_level"],
                eval_filter["year"],
                eval_filter["term"],
                eval_filter["instructor"],
            ),
        )
        for row in evaluation_rows:
            row["status"] = evaluation_status_label(row)
            row["other_degrees"] = query_all(
                conn,
                "SELECT DISTINCT name, level FROM DegreeCourseObjective "
                "WHERE course_no=%s AND objective_code=%s AND NOT (name=%s AND level=%s)",
                (row["course_no"], row["objective_code"], eval_filter["degree_name"], eval_filter["degree_level"]),
            )

    degree_query_filters = degree_query_data["filters"] if degree_query_data else {}
    course_query_filters = course_query_data["filters"] if course_query_data else {}
    instructor_query_filters = instructor_query_data["filters"] if instructor_query_data else {}
    eval_status_filters = eval_status_data["filters"] if eval_status_data else {}
    nonf_filters = nonf_data["filters"] if nonf_data else {}

    return render_template(
        "index.html",
        term_options=TERM_OPTIONS,
        messages=messages,
        errors=errors,
        degrees=degrees,
        courses=courses,
        instructors=instructors,
        semesters=semesters,
        objectives=objectives,
        dc_selection=dc_selection,
        dco_selection=dco_selection,
        eval_filter=eval_filter,
        degree_course_view=degree_course_view,
        dco_courses=dco_courses,
        dco_rows=dco_rows,
        evaluation_rows=evaluation_rows,
        degree_query_data=degree_query_data,
        course_query_data=course_query_data,
        instructor_query_data=instructor_query_data,
        eval_status_data=eval_status_data,
        nonf_data=nonf_data,
        degree_query_filters=degree_query_filters,
        course_query_filters=course_query_filters,
        instructor_query_filters=instructor_query_filters,
        eval_status_filters=eval_status_filters,
        nonf_filters=nonf_filters,
    )


if __name__ == "__main__":
    app.run(debug=True)
