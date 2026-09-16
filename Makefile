.PHONY: install dev test lint format security demo benchmark check

install:
	python -m pip install -e .

dev:
	python -m pip install -e '.[dev]'

test:
	pytest -q

lint:
	ruff check src tests benchmarks
	ruff format --check src tests benchmarks

format:
	ruff check src tests benchmarks --fix
	ruff format src tests benchmarks

security:
	bandit -q -r src
	pip-audit

demo:
	longgate inspect examples/demo.csv
	longgate run examples/demo.csv --backend demo

benchmark:
	python benchmarks/generate_adversarial.py
	python benchmarks/run_privacy_benchmark.py

check: test lint security
