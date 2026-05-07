# Project Assistant: Core Guidelines

You are the primary AI assistant for this project. Your goal is to write secure, efficient code and strictly minimize technical debt.
Put emphasis on security, code quality, maintainability, and adherence to best practices.
## 1. Tech Stack
- **Backend:** Python, Django
- **Database:** PostgreSQL (Strictly NO SQLite). Credentials must always use environment variables.
- **Frontend:** HTML, JavaScript, TailwindCSS (Always prioritize Tailwind classes for styling).
- **Code Quality:** Ruff (Linter & Formatter).

## 2. Core Commands
- **Run Server:** `python manage.py runserver`
- **Migrations:** `python manage.py makemigrations` and `python manage.py migrate`
- **Tests:** `python manage.py test`
- **Dependencies:** `pip install -r requirements.txt`
- **Format & Lint:** `ruff format .` and `ruff check .`

## 3. Documentation Architecture (Dispatcher Pattern)
This project uses an extended knowledge base. Before modifying complex logic or creating new apps, you **MUST ALWAYS** consult the relevant files:
- For structure and design patterns: read `docs/ARCHITECTURE.md`
- For Django models and DB rules: read `docs/DATABASE.md`
- For coding conventions, typing, and Ruff enforcement: read `docs/STYLEGUIDE.md`
- For automated testing strategy: read `docs/TESTING.md`

Never guess the database structure or existing patterns. If you are unsure, check the documentation in `docs/` or use CLI tools to actively analyze the codebase.