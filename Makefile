.PHONY: install dev test lint format security demo benchmark research-smoke research-summary check

install:
	python -m pip install -e .

dev:
	python -m pip install -e '.[dev]'

test:
	pytest -q

lint:
	ruff check src tests benchmarks research
	ruff format --check src tests benchmarks research

format:
	ruff check src tests benchmarks research --fix
	ruff format src tests benchmarks research

security:
	bandit -q -r src
	pip-audit

demo:
	longgate inspect examples/demo.csv
	longgate run examples/demo.csv --backend demo

benchmark:
	python benchmarks/generate_adversarial.py
	python benchmarks/run_privacy_benchmark.py

research-smoke:
	python -m research.run_experiments --config research/configs/paper-smoke.json --out research/results/paper-smoke
	python -m research.aggregate_results research/results/paper-smoke/runs.jsonl --out research/results/paper-smoke

research-summary:
	python -m research.aggregate_results research/results/paper-smoke/runs.jsonl --out research/results/paper-smoke

check: test lint security
