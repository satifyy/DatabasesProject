# Curriculum Assessment Toolkit

An end-to-end implementation of the degree/program assessment workflow described in the prompt. It uses:

- **MySQL** for the natural-key schema and sample dataset.
- **PHP + HTML** for the CRUD UI, evaluation cockpit, and required queries.
- **Python** utilities for repeatable provisioning and scripted reporting.

## 1. Installation & Environment

1. Install MySQL 8+, PHP 8+, and Python 3.10+ with `mysql-connector-python`.
2. Copy `config.ini`, update the `[database]` credentials (host/user/password/db name).
3. Provision the schema and sample data:
   ```bash
   python main.py --init --seed
   ```
   - `--init` applies `schema.sql` (natural PKs, FKs, CHECKs).
   - `--seed` loads `sample_data.sql` (two degrees, four courses, multiple objectives/sections/evaluations).
4. Start the PHP UI from the repo root:
   ```bash
   php -S localhost:8000 app.php
   ```
5. Visit [http://localhost:8000/index.html](http://localhost:8000/index.html) and follow the link to the portal.

`main.py --reset --yes` drops the database, letting you re-run init/seed cleanly.

## 2. Schema Summary (Phase 1)

| Table | PK | Highlights |
| ----- | -- | ---------- |
| `Degree(name, level, description)` | (name, level) | Natural composite key, CHECK on level set. |
| `Course(course_no, title, description)` | course_no | `title` unique. |
| `Instructor(instructor_id, name)` | instructor_id | Instructor names unique for UI clarity. |
| `Semester(year, term)` | (year, term) | CHECK restricts term ∈ {Spring,Summer,Fall}. |
| `Section(course_no, year, term, section_no, instructor_id, enrolled_count)` | (course_no, year, term, section_no) | FK → `Course`, `Semester`, `Instructor`; CHECK ensures non-negative enrollment. |
| `Objective(code, title, description)` | code | Describes measurable outcomes. |
| `DegreeCourse(name, level, course_no, is_core)` | (name, level, course_no) | FK → `Degree` & `Course`; CHECK on boolean; UI enforces ≥1 core per degree. |
| `DegreeCourseObjective(name, level, course_no, objective_code)` | (name, level, course_no, objective_code) | FK → `DegreeCourse` & `Objective`; UI prevents removing last objective for a core course or last course using an objective. |
| `Evaluation(course_no, year, term, section_no, name, level, objective_code, ...)` | (course_no, year, term, section_no, name, level, objective_code) | FK → `Section` & `DegreeCourseObjective`; CHECK ensures counts ≥ 0, `improvement_text` nullable. |

The schema exactly mirrors the ER model requirements: natural keys only, cascading deletes, and additional guard rails handled in PHP (degree must keep ≥1 core, core must retain objectives, etc.).

## 3. Sample Data

`sample_data.sql` seeds:

- Degrees: Computer Science (Bachelors) & Data Science (Masters).
- Courses: CS101, CS201, DS510, DS520.
- Objectives: OBJ1–OBJ4 covering problem solving, analysis, data management, communication.
- Sections across Spring/Fall 2023–2024 with three instructors.
- DegreeCourse links showing shared courses (CS201, DS520) to enable cross-degree copying.
- DegreeCourseObjective rows demonstrating core/elective mappings.
- Evaluation rows illustrating “complete”, “partial”, and “missing” states plus improvement notes.

## 4. Web Application Manual (Phase 2–4)

The portal (`app.php`) is broken into sections:

1. **Master Data** – CRUD forms + tables for Degree, Course, Instructor, Semester, Objective. All inputs are dropdowns/text boxes with per-row delete buttons.
2. **Degree–Course Assignment** – Select a degree, view every course, add/remove links, toggle core via checkbox. Business rules enforced: you cannot remove the last core or mark a course as core until it has objectives.
3. **Degree–Course–Objective Assignment** – Pick a degree, optionally limit to core courses, choose a course, and add/remove objectives via dropdowns.
4. **Section Entry** – Dropdowns for course/semester/instructor plus numeric enrollment input. Inserts or updates a section via natural key.
5. **Evaluation Workflow** – Implements the instructor flow:
   - Pick degree, semester, and instructor (Step 1).
   - Lists sections taught (Step 2) and expands objectives (Step 3).
   - Shows status badges (Step 4) and provides inline forms to edit method/counts/improvement (Step 5).
   - Copy panel duplicates an evaluation to another degree when the same course/objective exists (Step 6), validating DegreeCourseObjective membership.
   - Counts cannot exceed enrolled totals and are allowed to be partially filled.
6. **Required Queries** – Widgets for each reporting requirement:
   - Degree snapshot: courses + core flag, objectives, sections within a semester range, and courses tied to selected objectives.
   - Course sections over a range.
   - Instructor sections over a range.
   - Evaluation status per section for a semester (No/Partial/Complete + improvement presence).
   - Percent non-F query with threshold and enrolled-count validation.

All dropdowns are data-driven, no raw IDs are typed by the user. Transactions wrap each mutating action, ensuring consistent state.

## 5. Python Utilities (Phase 4 & 5 glue)

- `main.py`: provisioning CLI.
  - `--init` → run `schema.sql`.
  - `--seed` → run `sample_data.sql`.
  - `--reset --yes` → drop DB.
- `programfile.py`: reporting CLI mirroring the required queries.
  - `degree-courses NAME LEVEL`
  - `degree-sections NAME LEVEL START END`
  - `degree-objectives NAME LEVEL`
  - `degree-objective-courses NAME LEVEL OBJ ...`
  - `course-sections COURSE START END`
  - `instructor-sections INSTRUCTOR START END`
  - `eval-status YEAR TERM`
  - `nonf YEAR TERM THRESHOLD`
  - `demo` runs a scripted walkthrough hitting the above queries.

This satisfies the “users must not rely on SQL clients” constraint—everything is exposed via the UI or CLI.

## 6. Demo Walkthrough (Phase 5)

1. **Provision** – `python main.py --init --seed`.
2. **Master Data** – In the UI add another degree (e.g., “Software Engineering, Masters”).
3. **Degree–Course Assignment** – Link `CS201` and `DS520` to the new degree, mark as elective first, add objectives, then toggle to core.
4. **Degree–Course–Objective** – Assign OBJ1/OBJ3 to `DS520` via dropdown.
5. **Section Entry** – Add a Spring 2025 section (course, semester, instructor, enrollment).
6. **Evaluation** – Select the new semester/instructor, enter counts for each objective, save rows. Copy the evaluation to another degree when prompted.
7. **Queries** – Run the Degree snapshot to verify courses/objectives, the evaluation status widget to confirm No/Partial/Complete states, and the Non-F query with threshold `0.8`.

This sequence proves that the system can create a degree, assign courses/objectives, create semesters and sections, collect evaluations, duplicate evaluations across degrees, and run every required report without touching SQL manually.

## 7. Additional Notes

- All credentials live in `config.ini` only; PHP and Python load the same file.
- Natural-key FKs mean deleting a degree cascades through its assignments, objectives, and evaluations (per the ER model).
- PHP guard rails enforce logical constraints not easily expressed as SQL CHECKs (last core course, last objective, etc.).
- Percent-non-F ignores sections without totals or where totals exceed enrollment.
- `index.html` doubles as a lightweight landing page with launch instructions.

The repository therefore covers every requirement across schema, CRUD/UI, evaluation workflow, query layer, demo flow, and documentation.
