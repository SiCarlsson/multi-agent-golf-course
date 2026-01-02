###
# Local development commands
###
dev:
	@echo "Starting backend and frontend servers..."
	@trap 'kill 0' SIGINT; \
		./venv/bin/uvicorn backend.main:app --reload & \
		cd frontend && npm run dev

stop:
	@echo "Stopping servers..."
	@pkill -f "uvicorn backend.main:app" || true
	@pkill -f "vite" || true

###
# Docker commands
###
docker-rebuild:
	@echo "Rebuilding Docker containers without cache..."
	docker-compose build --no-cache && docker-compose up -d

docker-up:
	@echo "Starting Docker containers..."
	docker-compose up -d

docker-down:
	@echo "Stopping Docker containers..."
	docker-compose down
