"""
Détection d'anomalies par IsolationForest - version par SIRET.

Charge le model.pkl qui contient :
  - un modèle global (toutes les factures)
  - un modèle par SIRET (si assez de données pour ce fournisseur)

Si le SIRET a un modèle dédié, on l'utilise en priorité.
Sinon on fallback sur le modèle global.
"""

import pickle
from pathlib import Path

import numpy as np

MODEL_PATH = Path(__file__).parent.parent / "models" / "model.pkl"

# Chargement au démarrage
_global_model = None
_global_scaler = None
_siret_models = {}
_feature_names = []

if MODEL_PATH.exists():
    with open(MODEL_PATH, "rb") as f:
        artifact = pickle.load(f)
    _global_model = artifact["global"]["model"]
    _global_scaler = artifact["global"]["scaler"]
    _siret_models = artifact.get("siret_models", {})
    _feature_names = artifact["feature_names"]
    print(f"[ML] Modèle chargé : {artifact['n_samples']} samples, {artifact['n_siret_models']} modèles SIRET")
else:
    print(f"[ML] ATTENTION : {MODEL_PATH} introuvable. Lance 'python src/train.py' d'abord.")


def check_document(montant_ht, montant_ttc, tva_rate, ocr_confidence, siret=None) -> list[dict]:
    """
    Passe les features dans le modèle IsolationForest.
    Utilise le modèle spécifique au SIRET si disponible, sinon le global.
    """
    if _global_model is None or montant_ht is None:
        return []

    features = [
        montant_ht,
        montant_ttc if montant_ttc is not None else montant_ht * 1.2,
        tva_rate if tva_rate is not None else 20.0,
        ocr_confidence if ocr_confidence is not None else 0.93,
    ]

    X = np.array([features])

    # On choisit le bon modèle : spécifique au SIRET ou global
    if siret and siret in _siret_models:
        model = _siret_models[siret]["model"]
        scaler = _siret_models[siret]["scaler"]
        model_used = f"SIRET {siret}"
    else:
        model = _global_model
        scaler = _global_scaler
        model_used = "global"

    X_scaled = scaler.transform(X)
    prediction = model.predict(X_scaled)[0]
    score = model.score_samples(X_scaled)[0]

    if prediction == -1:
        deviations = abs(X_scaled[0])
        worst_idx = int(np.argmax(deviations))
        worst_feature = _feature_names[worst_idx]

        return [{
            "rule": "ML",
            "severity": "SUSPECT",
            "description": (
                f"Pattern anormal détecté par IsolationForest (score={score:.3f}, modèle={model_used}) : "
                f"montant_ht={montant_ht}, montant_ttc={montant_ttc}, "
                f"tva_rate={tva_rate}, ocr_confidence={ocr_confidence} "
                f"(feature la plus suspecte : {worst_feature})"
            ),
        }]

    return []
