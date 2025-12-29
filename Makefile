dev:
	@echo "Starting backend and frontend servers..."
	@trap 'kill 0' SIGINT; \
		./venv/bin/uvicorn backend.main:app --reload & \
		cd frontend && npm run dev

stop:
	@echo "Stopping servers..."
	@pkill -f "uvicorn backend.main:app" || true
	@pkill -f "vite" || true
