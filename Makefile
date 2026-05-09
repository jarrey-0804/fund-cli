.PHONY: help install test lint format clean build docker

help:
	@echo "Fund CLI v3.1 - 开发命令"
	@echo ""
	@echo "  make install    安装开发依赖"
	@echo "  make test       运行测试"
	@echo "  make lint       运行代码检查"
	@echo "  make format     格式化代码"
	@echo "  make build      构建包"
	@echo "  make docker     构建Docker镜像"
	@echo "  make clean      清理构建产物"

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --cov=fund_cli --cov-report=html

lint:
	ruff check src/
	mypy src/fund_cli/core/ src/fund_cli/data/ --ignore-missing-imports

format:
	black src/ tests/
	ruff check src/ --fix

build:
	python -m build

docker:
	docker build -t fund-cli:3.1.0 .
	docker tag fund-cli:3.1.0 fund-cli:latest

clean:
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
