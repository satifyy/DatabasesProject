"""Command-line helper for running required curriculum queries."""

from __future__ import annotations

import argparse
from typing import Tuple

import mysql.connector

from main import load_config

TERM_ORDER = {"Spring": 1, "Summer": 2, "Fall": 3}


def connect_db():
    cfg = load_config()
    return mysql.connector.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
    )


def parse_semester(label: str) -> Tuple[int, str]:
    try:
        year_str, term = label.split("-")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "semester must be in YEAR-Term format, e.g., 2024-Fall"
        ) from exc
    term = term.title()
    if term not in TERM_ORDER:
        raise argparse.ArgumentTypeError("term must be Spring, Summer, or Fall")
    return int(year_str), term


def semester_key(year: int, term: str) -> Tuple[int, int]:
    return year, TERM_ORDER[term]


def semester_between(record: Tuple[int, str], start: Tuple[int, str], end: Tuple[int, str]) -> bool:
    return semester_key(*start) <= semester_key(*record) <= semester_key(*end)


def fetch_rows(sql: str, params: tuple = ()):
    with connect_db() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
    return rows


def degree_courses(args):
    rows = fetch_rows(
        """
        SELECT dc.course_no, c.title, dc.is_core
        FROM DegreeCourse dc
        JOIN Course c ON c.course_no = dc.course_no
        WHERE dc.name=%s AND dc.level=%s
        ORDER BY c.course_no
        """,
        (args.name, args.level),
    )
    if not rows:
        print("No courses configured for that degree.")
        return
    for course_no, title, is_core in rows:
        status = "CORE" if is_core else "ELECTIVE"
        print(f"{course_no:<6} {title} [{status}]")


def degree_sections(args):
    rows = fetch_rows(
        """
        SELECT s.course_no, s.section_no, s.year, s.term, i.name
        FROM Section s
        JOIN DegreeCourse dc ON dc.course_no = s.course_no
            AND dc.name=%s AND dc.level=%s
        JOIN Instructor i ON i.instructor_id = s.instructor_id
        ORDER BY s.year, FIELD(s.term,'Spring','Summer','Fall'), s.course_no
        """,
        (args.name, args.level),
    )
    start = parse_semester(args.start)
    end = parse_semester(args.end)
    filtered = [row for row in rows if semester_between((row[2], row[3]), start, end)]
    if not filtered:
        print("No sections in that range.")
        return
    for course_no, section_no, year, term, inst in filtered:
        print(f"{year}-{term} {course_no}-{section_no} {inst}")


def degree_objectives(args):
    rows = fetch_rows(
        """
        SELECT DISTINCT o.code, o.title
        FROM DegreeCourseObjective dco
        JOIN Objective o ON o.code = dco.objective_code
        WHERE dco.name=%s AND dco.level=%s
        ORDER BY o.code
        """,
        (args.name, args.level),
    )
    for code, title in rows:
        print(f"{code}: {title}")


def degree_courses_for_objectives(args):
    if not args.objectives:
        print("Provide at least one objective code.")
        return
    placeholders = ",".join(["%s"] * len(args.objectives))
    sql = f"""
        SELECT DISTINCT dco.course_no, c.title, dco.objective_code
        FROM DegreeCourseObjective dco
        JOIN Course c ON c.course_no = dco.course_no
        WHERE dco.name=%s AND dco.level=%s AND dco.objective_code IN ({placeholders})
        ORDER BY dco.course_no
    """
    rows = fetch_rows(sql, (args.name, args.level, *args.objectives))
    if not rows:
        print("No matching courses for provided objectives.")
        return
    for course_no, title, objective in rows:
        print(f"{course_no} {title} <= {objective}")


def course_sections(args):
    rows = fetch_rows(
        """
        SELECT year, term, section_no, instructor_id
        FROM Section
        WHERE course_no=%s
        ORDER BY year, FIELD(term,'Spring','Summer','Fall'), section_no
        """,
        (args.course,),
    )
    start = parse_semester(args.start)
    end = parse_semester(args.end)
    filtered = [row for row in rows if semester_between((row[0], row[1]), start, end)]
    for year, term, section_no, instructor_id in filtered:
        print(f"{year}-{term} section {section_no} instructor {instructor_id}")


def instructor_sections(args):
    rows = fetch_rows(
        """
        SELECT course_no, section_no, year, term
        FROM Section
        WHERE instructor_id=%s
        ORDER BY year, FIELD(term,'Spring','Summer','Fall')
        """,
        (args.instructor,),
    )
    start = parse_semester(args.start)
    end = parse_semester(args.end)
    filtered = [row for row in rows if semester_between((row[2], row[3]), start, end)]
    for course_no, section_no, year, term in filtered:
        print(f"{year}-{term} {course_no}-{section_no}")


def evaluation_status(args):
    rows = fetch_rows(
        """
        WITH eval_rollup AS (
            SELECT course_no, year, term, section_no,
                   SUM(CASE WHEN method_label IS NOT NULL AND a_count IS NOT NULL AND b_count IS NOT NULL AND c_count IS NOT NULL AND f_count IS NOT NULL THEN 1 ELSE 0 END) AS complete_rows,
                   SUM(CASE WHEN method_label IS NULL OR a_count IS NULL OR b_count IS NULL OR c_count IS NULL OR f_count IS NULL THEN 1 ELSE 0 END) AS partial_rows,
                   SUM(CASE WHEN improvement_text IS NOT NULL AND improvement_text <> '' THEN 1 ELSE 0 END) AS improved_rows,
                   COUNT(*) AS total_rows
            FROM Evaluation
            WHERE year=%s AND term=%s
            GROUP BY course_no, year, term, section_no
        )
        SELECT s.course_no, s.section_no, c.title,
               COALESCE(er.total_rows, 0) AS total_rows,
               COALESCE(er.complete_rows, 0) AS complete_rows,
               COALESCE(er.partial_rows, 0) AS partial_rows,
               COALESCE(er.improved_rows, 0) AS improved_rows
        FROM Section s
        JOIN Course c ON c.course_no = s.course_no
        LEFT JOIN eval_rollup er ON er.course_no = s.course_no AND er.year = s.year AND er.term = s.term AND er.section_no = s.section_no
        WHERE s.year=%s AND s.term=%s
        ORDER BY s.course_no, s.section_no
        """,
        (args.year, args.term, args.year, args.term),
    )
    for course_no, section_no, title, total_rows, complete_rows, partial_rows, improved_rows in rows:
        if total_rows == 0:
            status = "No Evaluation"
        elif partial_rows > 0:
            status = "Partial"
        elif complete_rows == total_rows:
            status = "Complete"
        else:
            status = "Partial"
        has_improvement = "Yes" if improved_rows > 0 else "No"
        print(f"{course_no}-{section_no} {title} => {status} (Improvement: {has_improvement})")


def nonf_query(args):
    rows = fetch_rows(
        """
        WITH totals AS (
            SELECT course_no, year, term, section_no,
                   SUM(COALESCE(a_count,0) + COALESCE(b_count,0) + COALESCE(c_count,0)) AS nonf,
                   SUM(COALESCE(a_count,0) + COALESCE(b_count,0) + COALESCE(c_count,0) + COALESCE(f_count,0)) AS total
            FROM Evaluation
            WHERE year=%s AND term=%s
            GROUP BY course_no, year, term, section_no
        )
        SELECT s.course_no, s.section_no, c.title, t.nonf, t.total, s.enrolled_count
        FROM totals t
        JOIN Section s ON s.course_no=t.course_no AND s.year=t.year AND s.term=t.term AND s.section_no=t.section_no
        JOIN Course c ON c.course_no = s.course_no
        WHERE t.total > 0 AND (t.nonf / t.total) >= %s AND t.total <= s.enrolled_count
        ORDER BY s.course_no
        """,
        (args.year, args.term, args.threshold),
    )
    for course_no, section_no, title, nonf, total, enrolled in rows:
        pct = round(nonf / total, 3)
        print(f"{course_no}-{section_no} {title}: {nonf}/{total} = {pct} (enrolled {enrolled})")


def demo(_: argparse.Namespace):
    print("Demo: listing CS degree courses")
    degree_courses(argparse.Namespace(name="Computer Science", level="Bachelors"))
    print("\nDemo: CS degree objectives")
    degree_objectives(argparse.Namespace(name="Computer Science", level="Bachelors"))
    print("\nDemo: CS sections between 2023-Fall and 2024-Spring")
    deg_args = argparse.Namespace(name="Computer Science", level="Bachelors", start="2023-Fall", end="2024-Spring")
    degree_sections(deg_args)
    print("\nDemo: evaluation status for 2024 Spring")
    evaluation_status(argparse.Namespace(year=2024, term="Spring"))
    print("\nDemo: percent non-F >= 0.8 for Fall 2024")
    nonf_query(argparse.Namespace(year=2024, term="Fall", threshold=0.8))


def build_parser():
    parser = argparse.ArgumentParser(description="Run reporting queries against the curriculum DB.")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("degree-courses", help="List courses for a degree")
    p.add_argument("name")
    p.add_argument("level")
    p.set_defaults(func=degree_courses)

    p = sub.add_parser("degree-sections", help="List sections for a degree in a semester range")
    p.add_argument("name")
    p.add_argument("level")
    p.add_argument("start", help="e.g., 2023-Fall")
    p.add_argument("end", help="e.g., 2024-Spring")
    p.set_defaults(func=degree_sections)

    p = sub.add_parser("degree-objectives", help="List objectives for a degree")
    p.add_argument("name")
    p.add_argument("level")
    p.set_defaults(func=degree_objectives)

    p = sub.add_parser("degree-objective-courses", help="Courses tied to selected objectives")
    p.add_argument("name")
    p.add_argument("level")
    p.add_argument("objectives", nargs="+")
    p.set_defaults(func=degree_courses_for_objectives)

    p = sub.add_parser("course-sections", help="List sections for a course")
    p.add_argument("course")
    p.add_argument("start")
    p.add_argument("end")
    p.set_defaults(func=course_sections)

    p = sub.add_parser("instructor-sections", help="List sections taught by an instructor")
    p.add_argument("instructor")
    p.add_argument("start")
    p.add_argument("end")
    p.set_defaults(func=instructor_sections)

    p = sub.add_parser("eval-status", help="Evaluation rollup for a semester")
    p.add_argument("year", type=int)
    p.add_argument("term", choices=list(TERM_ORDER.keys()))
    p.set_defaults(func=evaluation_status)

    p = sub.add_parser("nonf", help="Percent non-F query")
    p.add_argument("year", type=int)
    p.add_argument("term", choices=list(TERM_ORDER.keys()))
    p.add_argument("threshold", type=float)
    p.set_defaults(func=nonf_query)

    p = sub.add_parser("demo", help="Run a scripted walkthrough")
    p.set_defaults(func=demo)

    return parser


def main(argv: list[str] | None = None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
