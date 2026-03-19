"""
Entraînement du modèle IsolationForest.
On entraîne un modèle global (toutes les factures) + un modèle par SIRET
quand on a assez d'historique pour ce fournisseur (>= 5 factures).

Usage :
    python train.py                              # données par défaut
    python train.py --data data/mes_factures.csv  # avec un CSV
"""

import argparse
import csv
import pickle
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

MODEL_PATH = Path(__file__).parent.parent / "models" / "model.pkl"
FEATURES = ["montant_ht", "montant_ttc", "tva_rate", "ocr_confidence"]
MIN_SAMPLES = 5  # en dessous on utilise le modèle global

# données de base pour tester sans CSV (2 fournisseurs avec des profils différents)
DEFAULT_DATA = [
    # fournisseur A — factures entre 1k et 8k
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
    # fournisseur B — factures entre 15k et 50k
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
    # quelques autres pour alimenter le modèle global
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
    """Charge les données depuis un CSV."""
    rows = []
    with open(path, "r") as f:
        for row in csv.DictReader(f):
            rows.append([row["siret"], float(row["montant_ht"]),
                         float(row["montant_ttc"]), float(row["tva_rate"]),
                         float(row["ocr_confidence"])])
    return rows


def _fit(data: np.ndarray, contamination=0.05) -> dict:
    """Entraîne un IsolationForest + StandardScaler sur un jeu de données."""
    scaler = StandardScaler()
    X = scaler.fit_transform(data)
    model = IsolationForest(contamination=contamination, random_state=42,
                            n_estimators=100)
    model.fit(X)
    return {"model": model, "scaler": scaler}


def train(raw_data: list):
    """Point d'entrée : entraîne le modèle global + les modèles par SIRET."""

    # on regroupe les factures par SIRET
    by_siret = defaultdict(list)
    all_features = []
    for row in raw_data:
        by_siret[row[0]].append(row[1:])
        all_features.append(row[1:])

    X_all = np.array(all_features)

    # 1) modèle global sur toutes les factures
    print(f"[Global] {len(X_all)} factures...")
    global_art = _fit(X_all)

    # 2) un modèle par SIRET si assez de données
    siret_models = {}
    for siret, feats in by_siret.items():
        if len(feats) >= MIN_SAMPLES:
            print(f"[SIRET {siret}] {len(feats)} factures")
            # contamination un peu plus haute car moins de données
            siret_models[siret] = _fit(np.array(feats), contamination=0.08)
        else:
            print(f"[SIRET {siret}] {len(feats)} factures → modèle global")

    # sauvegarde dans un seul .pkl
    artifact = {
        "global": global_art,
        "siret_models": siret_models,
        "feature_names": FEATURES,
        "n_samples": len(X_all),
        "n_siret_models": len(siret_models),
    }
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(artifact, f)

    print(f"\nSauvegardé dans {MODEL_PATH}")
    print(f"  {artifact['n_samples']} factures, {artifact['n_siret_models']} modèles SIRET")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, help="chemin vers un CSV")
    args = parser.parse_args()
    train(load_csv(args.data) if args.data else DEFAULT_DATA)
