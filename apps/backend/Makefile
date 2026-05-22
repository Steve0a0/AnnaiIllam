.PHONY: serve dev migrate seed-admin backup-db check-redis test

PYTHON := venv/Scripts/python.exe

serve:
	powershell -ExecutionPolicy Bypass -File serve.ps1

dev:
	$(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	$(PYTHON) -m alembic upgrade head

seed-admin:
	$(PYTHON) -m scripts.seed_admin --email "$(EMAIL)" --password "$(PASSWORD)" --name "$(NAME)"

backup-db:
	$(PYTHON) -m scripts.backup_postgres

check-redis:
	$(PYTHON) -m scripts.check_redis

test:
	$(PYTHON) -m pytest
