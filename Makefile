.PHONY: install test lint run baseline cert ablate adversarial clean

install:
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check src tests experiments

run:
	python -m cert_lgs.cli --config configs/default.yaml

baseline:
	python experiments/run_baselines.py --config configs/default.yaml

cert:
	python experiments/run_cert_lgs.py --config configs/default.yaml

ablate:
	python experiments/run_ablations.py --config configs/default.yaml

adversarial:
	python experiments/run_adversarial_tests.py --config configs/adversarial.yaml

clean:
	rm -rf results/raw/* results/tables/* results/figures/* .pytest_cache .ruff_cache
