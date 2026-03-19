"""
Détection d'anomalies via IsolationForest.
On a un modèle par SIRET (quand y'a assez d'historique) + un modèle global en fallback.
Le .pkl est chargé une seule fois au démarrage du service.
"""

import pickle
from pathlib import Path
import numpy as np

MODEL_PATH = Path(__file__).parent.parent / "models" / "model.pkl"

_global_model = None
_global_scaler = None
_siret_models = {}
_feature_names = []

# chargement du modèle au démarrage
if MODEL_PATH.exists():
    with open(MODEL_PATH, "rb") as f:
        artifact = pickle.load(f)
    _global_model = artifact["global"]["model"]
    _global_scaler = artifact["global"]["scaler"]
    _siret_models = artifact.get("siret_models", {})
    _feature_names = artifact["feature_names"]
    print(f"[ML] Modèle chargé — {artifact['n_samples']} samples, "
          f"{artifact['n_siret_models']} modèles SIRET")
else:
    print(f"[ML] {MODEL_PATH} introuvable, lance train.py d'abord")


def check_document(montant_ht, montant_ttc, tva_rate, ocr_confidence,
                   siret=None) -> list[dict]:
    """Passe les features dans l'IsolationForest.
    Prend le modèle spécifique au SIRET si dispo, sinon le global."""

    if _global_model is None or montant_ht is None:
        return []

    # on construit le vecteur de features (valeurs par défaut si manquantes)
    features = [
        montant_ht,
        montant_ttc or montant_ht * 1.2,
        tva_rate if tva_rate is not None else 20.0,
        ocr_confidence or 0.93,
    ]
    X = np.array([features])

    # choix du modèle : spécifique au fournisseur ou global
    if siret and siret in _siret_models:
        model = _siret_models[siret]["model"]
        scaler = _siret_models[siret]["scaler"]
        model_name = f"SIRET {siret}"
    else:
        model = _global_model
        scaler = _global_scaler
        model_name = "global"

    X_scaled = scaler.transform(X)
    pred = model.predict(X_scaled)[0]
    score = model.score_samples(X_scaled)[0]

    # -1 = anomalie détectée par l'IsolationForest
    if pred == -1:
        # on regarde quelle feature dévie le plus pour donner du contexte
        worst = _feature_names[int(np.argmax(abs(X_scaled[0])))]
        return [{"rule": "ML", "severity": "SUSPECT",
                 "description": (
                     f"Pattern anormal détecté par IsolationForest "
                     f"(score={score:.3f}, modèle={model_name}) : "
                     f"montant_ht={montant_ht}, montant_ttc={montant_ttc}, "
                     f"tva_rate={tva_rate}, ocr_confidence={ocr_confidence} "
                     f"(feature la plus suspecte : {worst})")}]
    return []
