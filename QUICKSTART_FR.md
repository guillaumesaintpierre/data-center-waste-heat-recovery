# Démarrage rapide — Données danoises et GitHub

Ce dépôt est une étude thermodynamique **exploratoire**. Le rapport et les résultats déjà inclus reposent sur des hypothèses. Le second scénario utilise des données historiques uniquement après téléchargement et contrôle sur un ordinateur connecté.

## A — Vérifier le projet

Dans le Terminal macOS, place-toi dans le dossier qui contient `run.py`, puis :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python -m pytest -q
python run.py
```

## B — Ajouter les températures et prix réels (2025)

```bash
python scripts/fetch_real_inputs.py --year 2025
python run.py --config config.real-2025.json --out results/real-2025
python scripts/plot_observed_inputs.py --year 2025
python scripts/compare_runs.py
```

Les fichiers apparaîtront dans `data/observed/`, avec un document `observed_2025.metadata.json` indiquant les fournisseurs, les URL, les contrôles et les valeurs interpolées éventuelles. Le dossier `results/real-2025` contiendra les résultats du scénario avec **prix et températures observés**, mais où consommation informatique et demande de chaleur restent **modélisées**.

Si le téléchargement échoue, **ne remplace pas les mesures par des données fictives** et ne présente pas les résultats de référence comme des résultats historiques. Copie le message d'erreur pour pouvoir le diagnostiquer.

## C — Publier sur GitHub

Crée d'abord un dépôt public **vide** nommé `data-center-waste-heat-recovery` sur https://github.com/new, sans README ni licence automatiques.

```bash
git init -b main
git add .
git status
git commit -m "Add thermodynamic model, verification tests and observed-data pipeline"
git remote add origin https://github.com/guillaumesaintpierre/data-center-waste-heat-recovery.git
git push -u origin main
```

Vérifie que les tests GitHub Actions passent et que les fichiers `data/observed/` sont présents **seulement s'ils ont été réellement téléchargés**. Tu pourras ensuite intégrer les résultats de ce second scénario au rapport.

Pour les détails scientifiques : `docs/OBSERVED_DATA_2025.md`. Pour le protocole de publication : `GITHUB_SETUP.md`.
