"""
Script d'entraînement du modèle IsolationForest.
Entraîne un modèle global + un modèle par SIRET (si assez de données).

Usage :
    python -m src.train                     # données hardcodées
    python -m src.train --data data/mes_factures.csv # données réelles
"""

import argparse
import pickle
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

MODEL_PATH = Path(__file__).parent.parent / "models" / "model.pkl"
FEATURE_NAMES = ["montant_ht", "montant_ttc", "tva_rate", "ocr_confidence"]

MIN_SAMPLES_PER_SIRET = 5

DEFAULT_DATA = [
    ["44306184100047", 1000, 1200, 20.0, 0.95],
    ["44306184100047", 2000, 2400, 20.0, 0.93],
    ["44306184100047", 3000, 3600, 20.0, 0.96],
    ["44306184100047", 4000, 4800, 20.0, 0.91],
    ["44306184100047", 5000, 6000, 20.0, 0.94],
    ["44306184100047", 6000, 7200, 20.0, 0.92],
    ["44306184100047", 7000, 8400, 20.0, 0.97],
    ["44306184100047", 8000, 9600, 20.0, 0.90],
    ["44306184100047", 3500, 4200, 20.0, 0.93],
    ["44306184100047", 4500, 5400, 20.0, 0.95],
    ["44306184100047", 2500, 3000, 20.0, 0.94],
    ["44306184100047", 5500, 6600, 20.0, 0.92],
    ["10000000410009", 15000, 18000, 20.0, 0.94],
    ["10000000410009", 20000, 24000, 20.0, 0.92],
    ["10000000410009", 25000, 30000, 20.0, 0.96],
    ["10000000410009", 30000, 36000, 20.0, 0.91],
    ["10000000410009", 35000, 42000, 20.0, 0.93],
    ["10000000410009", 40000, 48000, 20.0, 0.95],
    ["10000000410009", 45000, 54000, 20.0, 0.94],
    ["10000000410009", 18000, 21600, 20.0, 0.92],
    ["10000000410009", 22000, 26400, 20.0, 0.96],
    ["10000000410009", 28000, 33600, 20.0, 0.93],
    ["10000000410009", 32000, 38400, 20.0, 0.91],
    ["10000000410009", 38000, 45600, 20.0, 0.95],
    ["99999999999999", 500, 600, 20.0, 0.95],
    ["99999999999999", 750, 900, 20.0, 0.93],
    ["88888888888888", 800, 844, 5.5, 0.93],
    ["88888888888888", 1500, 1582.5, 5.5, 0.95],
    ["77777777777777", 2000, 2200, 10.0, 0.96],
    ["77777777777777", 4000, 4400, 10.0, 0.91],
    ["66666666666666", 5000, 5000, 0.0, 0.94],
    ["66666666666666", 10000, 10000, 0.0, 0.92],
]


def load_csv(path: str) -> list:
    """Charge un CSV : siret,montant_ht,montant_ttc,tva_rate,ocr_confidence"""
    import csv
    rows = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append([
                row["siret"],
                float(row["montant_ht"]),
                float(row["montant_ttc"]),
                float(row["tva_rate"]),
                float(row["ocr_confidence"]),
            ])
    return rows


def _train_one(data: np.ndarray, contamination: float = 0.05) -> dict:
    """Entraîne un modèle + scaler sur un jeu de données."""
    scaler = StandardScaler()
    X = scaler.fit_transform(data)
    model = IsolationForest(contamination=contamination, random_state=42, n_estimators=100)
    model.fit(X)
    return {"model": model, "scaler": scaler}


def train(raw_data: list):
    """Entraîne le modèle global + les modèles par SIRET."""
    by_siret = defaultdict(list)
    all_features = []
    for row in raw_data:
        siret = row[0]
        features = row[1:]
        by_siret[siret].append(features)
        all_features.append(features)

    all_features = np.array(all_features)

    print(f"[Global] Entraînement sur {len(all_features)} factures...")
    global_artifact = _train_one(all_features)

    siret_models = {}
    for siret, features in by_siret.items():
        if len(features) >= MIN_SAMPLES_PER_SIRET:
            print(f"[SIRET {siret}] Entraînement sur {len(features)} factures...")
            siret_models[siret] = _train_one(np.array(features), contamination=0.08)
        else:
            print(f"[SIRET {siret}] {len(features)} factures (< {MIN_SAMPLES_PER_SIRET}) -> modèle global")

    artifact = {
        "global": global_artifact,
        "siret_models": siret_models,
        "feature_names": FEATURE_NAMES,
        "n_samples": len(all_features),
        "n_siret_models": len(siret_models),
    }

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(artifact, f)

    print(f"\nModèle sauvegardé dans {MODEL_PATH}")
    print(f"  - Total factures : {artifact['n_samples']}")
    print(f"  - Modèles SIRET  : {artifact['n_siret_models']}")
    for siret in siret_models:
        print(f"    - {siret} ({len(by_siret[siret])} factures)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Entraîne le modèle IsolationForest")
    parser.add_argument("--data", type=str, help="Chemin vers un CSV")
    args = parser.parse_args()

    data = load_csv(args.data) if args.data else DEFAULT_DATA
    train(data)
