.PHONY: install dev test lint format security demo benchmark research-check research-smoke research-summary research-redteam check

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

research-check:
	python -m research.check_artifact

research-redteam:
	python -m research.semantic_redteam --corpus research/redteam/semantic_synthetic_v1.jsonl --baseline identity --baseline deterministic-regex --out research/results/paper-smoke
	python -m research.release_boundary_redteam --out research/results/paper-smoke

research-smoke: research-check
	python -m research.run_experiments --config research/configs/paper-smoke.json --out research/results/paper-smoke
	python -m research.aggregate_results research/results/paper-smoke/runs.jsonl --out research/results/paper-smoke
	$(MAKE) research-redteam

research-summary:
	python -m research.aggregate_results research/results/paper-smoke/runs.jsonl --out research/results/paper-smoke

check: test lint security research-check
