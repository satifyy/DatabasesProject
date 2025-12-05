# Curriculum Assessment Flask App

The project instructions in `docs/2.txt` (lines 53‑56) require **“a brief installation/user manual”** targeted at a junior CS student who has not taken a database course. This guide walks through every step needed to set up the MySQL database, configure the Flask app, and use the portal locally.

## 1. Prerequisites

1. **Python 3.11+** – download from [python.org/downloads](https://www.python.org/downloads/) and check with `python --version`.
2. **pip** – bundled with modern Python; verify with `python -m pip --version`.
3. **Git** – optional but helpful for cloning the repo.
4. **MySQL** – install from [dev.mysql.com/downloads/mysql](https://dev.mysql.com/downloads/mysql) (or MariaDB but these instructions were tested on MySQL). During installation, note the root password you choose and allow the service to start automatically.
5. (Optional) **MySQL Workbench** – GUI for running SQL scripts if you prefer not to use the command line these instructions will be based in the command line.

## 2. Create the Database

1. Start the MySQL service (Windows Services panel, `brew services start mysql`, or `systemctl start mysql` depending on OS).
2. Open a terminal and launch the MySQL shell:
   ```bash
   mysql -u root -p
   ```
3. Inside the shell, create the database user the apps expect:
   ```sql
   CREATE DATABASE IF NOT EXISTS curriculum_tracker CHARACTER SET utf8mb4;
   CREATE USER IF NOT EXISTS 'cs_user'@'localhost' IDENTIFIED BY 'cs_pass';
   GRANT ALL PRIVILEGES ON curriculum_tracker.* TO 'cs_user'@'localhost';
   FLUSH PRIVILEGES;
   ```
   Feel free to replace `cs_user` / `cs_pass` with safer credentials; just keep them handy for the next step.

## 3. Apply the Schema and Sample Data

Run the provided SQL files from the project root (one level above `flask_app/`).

```bash
cd /path/to/Project
mysql -u cs_user -p curriculum_tracker < schema.sql
# Optional: load demo data to see degrees/courses immediately
mysql -u cs_user -p curriculum_tracker < sample_data.sql
```

If you prefer Workbench, open each `.sql` file there and execute it.

## 4. Configure the Flask App

1. Copy the example configuration and edit it:
   ```bash
   cd flask_app
   cp config.ini.example config.ini
   ```
2. Update `config.ini` so the `[database]` values match the credentials you created (`host`, `port`, `user`, `password`, `database`).

## 5. Install Python Dependencies

```bash
cd flask_app
python -m venv .venv            # optional but recommended
# Activate the virtualenv:
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

This installs Flask, PyMySQL, and python-dotenv.

## 6. Run the Application

1. Ensure the MySQL server is still running.
2. From `flask_app/`, start the dev server:
   ```bash
   flask --app app run --debug
   # or: python app.py
   ```
3. Open a browser to <http://127.0.0.1:5000>. The “Curriculum Assessment Portal” UI should load.

## 7. Using the Portal

- **Master Data**: Enter degrees, courses, instructors, semesters, and objectives using the forms on the landing page. Each form saves records directly to MySQL.
- **Degree ↔ Course / Objectives**: Select an existing degree to assign courses, mark them core/elective, and attach objectives.
- **Section Entry**: Pick a course, semester, section number, instructor, and enrollment count to create sections.
- **Evaluation Workflow**: Choose degree + semester + instructor to load all required rows, then enter assessment data (method, counts, improvements). Use the “Copy evaluation” action to duplicate work across degrees.
- **Reports**: Use the Degree/Course/Instructor queries, Evaluation Status, and Non-F% reports at the bottom to inspect data and verify completeness.

All form submissions happen on the same page, so after you save a record, scroll to confirm the success or error message. If something fails (e.g., missing required fields or constraint violations), the red error card at the top explains what to fix.

## 8. Troubleshooting

- **Cannot connect to database**: Verify `config.ini` credentials, confirm MySQL is running, and ensure the `curriculum_tracker` schema exists.
- **Missing tables**: Re-run `schema.sql` and restart the Flask server.
- **Permission denied when running SQL files**: Log in as the MySQL root user, rerun the GRANT statements, or adjust the account’s privileges.
- **Port conflict on 5000**: Run `flask --app app run --debug --port 5050` and visit `http://127.0.0.1:5050`.

With these steps, a junior CS student (even without database experience) can install MySQL, prepare the schema, configure the app, and begin using the portal locally.
