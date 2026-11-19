# Publish the energy engineering project on GitHub

The project is **not yet uploaded** to your account. The GitHub connector can edit existing repositories but cannot create a new public repository in this session. Do not overwrite your robotics repos.

## 1 — Create the empty repository

Visit https://github.com/new (signed in as `guillaumesaintpierre`). Use repository name `data-center-waste-heat-recovery`, description `Hourly thermodynamic and techno-economic screening of data-centre waste-heat recovery for district heating`. Set visibility Public and **do not** select README, .gitignore or license (this archive already includes all three). Press **Create repository**.

## 2 — Prepare the files on your Mac

Extract the ZIP; in Terminal, change directory to the folder containing `run.py` (not its parent):

```bash
cd ~/Downloads/data-center-waste-heat-recovery
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python -m pytest -q
python run.py
```

## 3 — Retrieve 2025 observed data on your Mac

Requires a working internet connection. The repository already contains a fully implemented fetcher, but no historical CSVs were downloaded in the hosted environment.

```bash
python scripts/fetch_real_inputs.py --year 2025
python run.py --config config.real-2025.json --out results/real-2025
python scripts/plot_observed_inputs.py --year 2025
python scripts/compare_runs.py
```

If this raises a provider error, *do not* commit fake data or label the synthetic figures as measured. Note the exact error and resolve station coverage, data availability or schema. If weather has gaps exceeding the declared interpolation threshold, discuss the missingness before choosing another station or method.

**Check before uploading:** inspect `data/observed/observed_2025.metadata.json`, the two CSVs, and `results/real-2025/summary.json`. The latter must name observed data in `provenance`. The bundled PDF covers the *synthetic baseline*, not the new 2025 scenario.

## 4 — Publish the repository

```bash
git init -b main
git add .
git status
git commit -m "Build validated waste-heat screening model and historical data import"
git remote add origin https://github.com/guillaumesaintpierre/data-center-waste-heat-recovery.git
git push -u origin main
```

GitHub may request browser sign-in. Use the Git Credential Manager or `gh auth login` on your Mac if necessary; never paste access tokens into chat.

## 5 — Check publication

- GitHub Actions `Validation` workflow passes.
- README openly identifies baseline synthetic outputs and the optional (downloaded) historical run.
- Source credit includes DMI and Energinet (CC BY 4.0).
- Historical CSV metadata lists exact requests, observation counts and SHA-256 hashes.
- README plots are baseline unless deliberately replaced **after** reviewing measured-input results.
- Use `git status` after publication; it should say the working tree is clean.

## Scientific language for CV (only when you have run and reviewed the complete historical case)

`Implemented and verified an hourly Python model of data-centre waste heat recovery, integrating Danish electricity-market prices and DMI weather observations to assess thermodynamic operation, demand matching and economic sensitivity.`

Avoid saying *validated against an operating plant*; there are no operating-plant measurements.
