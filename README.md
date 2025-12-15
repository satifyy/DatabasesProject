# Curriculum Assessment Flask App


## 1. Prerequisites

1. **Python 3.11+** – download from [python.org/downloads](https://www.python.org/downloads/) and check with `python --version`.
2. **pip** – bundled with modern Python; verify with `python -m pip --version`.
3. **MySQL** – install from [dev.mysql.com/downloads/mysql](https://dev.mysql.com/downloads/mysql) (or MariaDB but these instructions were tested on MySQL). During installation, note the root password you choose and allow the service to start automatically.
4. (Optional) **MySQL Workbench** – GUI for running SQL scripts if you prefer not to use the command line these instructions will be based in the command line.

## 2. Create the Database

1. Start the MySQL service 
    - **Windows:** Press `Win + R`, type `services.msc`, press Enter. Find "MySQLxx" and start it. Or run: `net start MySQLxx`
   - **macOS:** `brew services start mysql`
   - **Linux:** `sudo systemctl start mysql`

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

Run the provided SQL files from the project root (one level above `DatabaseProjectFlaskApp/`).

```bash
cd /path/to/Project
mysql -u cs_user -p curriculum_tracker < schema.sql
# Optional: load demo data to see degrees/courses immediately
mysql -u cs_user -p curriculum_tracker < test_sample_data.sql
```

If you prefer Workbench, open each `.sql` file there and execute it.

## 4. Configure the Flask App

1. Copy the example configuration and edit it:
   ```bash
   cd DatabaseProjectFlaskApp
   cp config.ini.example config.ini
   ```
2. Update `config.ini` so the `[database]` values match the credentials you created (`host`, `port`, `user`, `password`, `database`). The template already shows the required keys:
   ```ini
   [database]
   host = localhost
   port = 3306
   user = cs_user
   password = cs_pass
   database = curriculum_tracker
   ```

## 5. Install Python Dependencies

```bash
cd DatabaseProjectFlaskApp
python -m venv .venv            # optional but recommended
# Activate the virtualenv:
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

This installs Flask, PyMySQL, and python-dotenv.

## 6. Run the Application

1. Ensure the MySQL server is still running.
2. From `DatabaseProjectFlaskApp/`, start the dev server:
   ```bash
   flask --app app run --debug
   # or: python app.py
   ```
3. Open a browser to <http://127.0.0.1:5000>. The “Curriculum Assessment Portal” UI should load.

## 7. Using the Portal

The app is organized into focused pages so new users can follow the exact workflow from the project spec:

1. **Manage Degrees** – create BA/BS/MS/Ph.D./Cert programs, attach catalog courses, mark core requirements, and map objectives per course (the Degree–Course–Objective mapping lives entirely here).
2. **Manage Courses** – maintain the course catalog and instructor directory.
3. **Manage Objectives** – define learning objectives (120-char titles with unique constraint).
4. **Manage Semesters & Sections** – add semesters, then create sections with 3-digit section numbers, instructor assignments, and enrollment counts.
5. **Enter/Review Evaluations** – pick a degree, semester, and instructor to see each section’s required objectives, enter assessment data, view the “X / Y evaluated (Z%)” summary plus missing codes, and copy an evaluation from one degree to another when courses/objectives overlap.
6. **Run Queries / Reports** – execute the required SQL-driven reports:
   - degree-specific course/objective/section listings,
   - degree objective → courses lookup,
   - course and instructor history within a semester range,
   - evaluation status per semester,
   - non-F percentage filter for a semester.

Each form posts to its own page and immediately flashes success/error messages at the top. Once you configure master data, move left-to-right through the navigation for a predictable workflow.

## 8. Troubleshooting

- **Cannot connect to database**: Verify `config.ini` credentials, confirm MySQL is running, and ensure the `curriculum_tracker` schema exists.
- **Missing tables**: Re-run `schema.sql` and restart the Flask server.
- **Permission denied when running SQL files**: Log in as the MySQL root user, rerun the GRANT statements, or adjust the account’s privileges.
- **Port conflict on 5000**: Run `flask --app app run --debug --port 5050` and visit `http://127.0.0.1:5050`.
