
.PHONY: dev backend frontend install test lint seed docker-build

dev: ## Start backend + frontend dev servers
	@echo '>>> Starting DarkLead dev stack'
	@cd backend && uvicorn app.main:app --reload --port 7860 &
	@cd frontend && npm run dev

backend: ## Start backend only
	cd backend && uvicorn app.main:app --reload --port 7860

frontend: ## Start frontend dev server
	cd frontend && npm run dev

install: ## Install all dependencies
	cd backend && pip install -r requirements.txt --break-system-packages
	cd frontend && npm install --legacy-peer-deps

test: ## Run all tests
	cd backend && pytest tests/ -v

lint: ## Run ruff + vue-tsc
	cd backend && ruff check app/
	cd frontend && npx vue-tsc --noEmit

seed: ## Seed demo data
	cd backend && python seed_demo.py

docker-build: ## Build Docker image
	docker build -t darklead:latest .

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS=":.*##"}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
