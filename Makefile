.PHONY: help install test demo clean docker-build docker-run lint format

help:
	@echo "AI-Powered LEGO Architect - Development Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make install      - Install dependencies in virtual environment"
	@echo "  make test         - Run all test suites"
	@echo "  make demo         - Run interactive demo"
	@echo "  make demo-llm     - Run AI-powered demo (requires API key)"
	@echo "  make lint         - Run code linters"
	@echo "  make format       - Format code with black"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run in Docker container"
	@echo "  make clean        - Remove build artifacts"

install:
	@echo "🔧 Installing dependencies..."
	@./install.sh

test:
	@echo "🧪 Running tests..."
	@./test.sh

demo:
	@echo "🎮 Running demo..."
	@python3 demo.py

demo-llm:
	@echo "🤖 Running AI-powered demo..."
	@python3 demo_llm.py

demo-orchestrator:
	@echo "🎭 Running orchestrator demo..."
	@python3 demo_orchestrator.py

lint:
	@echo "🔍 Running linters..."
	@ruff check lego_architect/ || true
	@mypy lego_architect/ || true

format:
	@echo "✨ Formatting code..."
	@black lego_architect/ tests/ *.py

docker-build:
	@echo "🐳 Building Docker image..."
	@docker-compose build

docker-run:
	@echo "🚀 Running in Docker..."
	@./run_docker.sh

clean:
	@echo "🧹 Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf build/ dist/ .coverage htmlcov/ 2>/dev/null || true
	@echo "✅ Cleaned!"
