install:
	python -m pip install -r requirements.txt
	cd frontend && npm install

run-backend:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	cd frontend && npm run dev

run:
	@echo "To run both, run 'make run-backend' and 'make run-frontend' in separate terminals, or 'docker compose up -d'"

seed:
	python scripts/seed_exasol.py
	python scripts/seed_postgres.py

demo:
	python -m app.demo

test:
	pytest -q
