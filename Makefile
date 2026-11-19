.PHONY: test baseline observed compare

test:
	PYTHONPATH=src python -m pytest -q

baseline:
	python run.py --config config.json --out results

observed:
	python scripts/fetch_real_inputs.py --year 2025
	python run.py --config config.real-2025.json --out results/real-2025
	python scripts/plot_observed_inputs.py --year 2025

compare:
	python scripts/compare_runs.py --reference results/summary.json --observed results/real-2025/summary.json
