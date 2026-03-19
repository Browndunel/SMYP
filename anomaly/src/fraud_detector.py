"""
Moteur de règles métier (R1 → R7) + appel au modèle ML.
C'est ici qu'on vérifie la cohérence des documents entre eux
et qu'on détecte les trucs louches (SIRET bidon, TVA inventée, etc.)
"""

import re
import time
from datetime import date
from typing import Any
from ml_detector import check_document


# mapping type API → type interne (juste pour simplifier les comparaisons)
DOC_TYPE_MAP = {
    "FACTURE": "facture", "DEVIS": "devis",
    "ATTESTATION_SIRET": "siret", "ATTESTATION_URSSAF": "urssaf",
    "EXTRAIT_KBIS": "kbis", "RIB": "rib",
}

# certains champs s'appellent différemment selon le doc
# ex: "fournisseur" sur une facture = "nom_entreprise" sur un Kbis
FIELD_ALIASES = {
    "fournisseur": "nom_entreprise",
    "nom_titulaire": "nom_entreprise",
    "tva_rate": "tva",
    "date_emission": "date_emission",
    "date_expiration": "date_expiration",
}

TVA_TAUX_LEGAUX = {0.0, 5.5, 10.0, 20.0}  # taux autorisés en France

# poids pour le calcul du score final
SEVERITY_WEIGHT = {"FRAUDULEUX": 0.30, "SUSPECT": 0.12}
SEVERITY_OUTPUT = {"FRAUDULEUX": "high", "SUSPECT": "medium"}


# ---------- utilitaires ----------

def _norm(val: Any) -> str:
    """Minuscule + espaces unifiés, pour comparer deux valeurs."""
    if val is None:
        return ""
    return re.sub(r"\s+", " ", str(val).lower().strip())


def _to_float(val: Any) -> float | None:
    """Convertit en float en gérant les virgules et symboles (€, etc.)."""
    if val is None:
        return None
    try:
        return float(re.sub(r"[^\d.,\-]", "", str(val)).replace(",", "."))
    except (ValueError, TypeError):
        return None


def _normalize_fields(fields) -> dict:
    """Applique les alias pour uniformiser les noms de champs."""
    if hasattr(fields, "model_dump"):
        fields = fields.model_dump()
    elif not isinstance(fields, dict):
        fields = dict(fields)
    out = {}
    for k, v in fields.items():
        out[FIELD_ALIASES.get(k, k)] = v
    for k, v in fields.items():
        if k not in out:
            out[k] = v
    return out


def _resolve_type(raw: str) -> str:
    return DOC_TYPE_MAP.get(raw, raw.lower())


# ---------- règles R1 à R7 ----------

def _r1_siret_coherent(main_type, main_f, rel_type, rel_f):
    """R1 — le SIRET doit être identique entre le doc principal et ses docs liés."""
    a, b = main_f.get("siret"), rel_f.get("siret")
    if not a or not b or _norm(a) == _norm(b):
        return []
    return [{"rule": "R1", "severity": "FRAUDULEUX",
             "description": f"SIRET incohérent : {main_type.upper()}={a} / {rel_type.upper()}={b}"}]


def _r2_urssaf_expiration(doc_type, fields):
    """R2 — une attestation URSSAF expirée n'est plus valable."""
    if doc_type != "urssaf":
        return []
    raw = fields.get("date_expiration") or fields.get("date_validite")
    if not raw:
        return []
    try:
        if date.fromisoformat(str(raw)) < date.today():
            return [{"rule": "R2", "severity": "FRAUDULEUX",
                     "description": f"Attestation URSSAF expirée : date_expiration={raw} < aujourd'hui"}]
    except ValueError:
        pass
    return []


def _r3_tva_taux_legal(fields):
    """R3 — le taux de TVA doit être 0%, 5.5%, 10% ou 20%."""
    tva = _to_float(fields.get("tva"))
    if tva is None or tva in TVA_TAUX_LEGAUX:
        return []
    return [{"rule": "R3", "severity": "SUSPECT",
             "description": f"Taux de TVA non légal : {tva}% (attendu : 0%, 5.5%, 10% ou 20%)"}]


def _r4_calcul_ttc(fields):
    """R4 — on recalcule HT + TVA et on compare au TTC annoncé (tolérance 0.02€)."""
    ht, ttc, tva = _to_float(fields.get("montant_ht")), _to_float(fields.get("montant_ttc")), _to_float(fields.get("tva"))
    if ht is None or ttc is None or tva is None:
        return []
    expected = round(ht * (1 + tva / 100), 2)
    ecart = abs(expected - ttc)
    if ecart <= 0.02:
        return []
    return [{"rule": "R4", "severity": "SUSPECT",
             "description": f"Calcul TTC incohérent : HT={ht} + TVA {tva}% = {expected}, mais TTC={ttc} (écart={ecart:.2f}€)"}]


def _r5_iban_format(fields):
    """R5 — vérifie le format IBAN (longueur FR=27 + checksum modulo 97, norme ISO 13616)."""
    iban = fields.get("iban")
    if not iban:
        return []
    clean = re.sub(r"\s", "", str(iban)).upper()

    if clean.startswith("FR") and len(clean) != 27:
        return [{"rule": "R5", "severity": "SUSPECT",
                 "description": f"IBAN format invalide : longueur={len(clean)} (attendu 27 pour FR) : {iban}"}]

    if not re.match(r"^[A-Z]{2}\d{2}[A-Z0-9]+$", clean):
        return [{"rule": "R5", "severity": "SUSPECT",
                 "description": f"IBAN format invalide : {iban}"}]

    # checksum ISO 13616 : on déplace les 4 premiers chars à la fin,
    # lettres → chiffres (A=10, B=11…), puis modulo 97 doit donner 1
    moved = clean[4:] + clean[:4]
    numeric = "".join(str(ord(c) - 55) if c.isalpha() else c for c in moved)
    if int(numeric) % 97 != 1:
        return [{"rule": "R5", "severity": "SUSPECT",
                 "description": f"IBAN checksum invalide (modulo 97) : {iban}"}]
    return []


def _r6_date_emission(fields):
    """R6 — la date d'émission ne peut pas être dans le futur."""
    raw = fields.get("date_emission")
    if not raw:
        return []
    try:
        if date.fromisoformat(str(raw)) > date.today():
            return [{"rule": "R6", "severity": "SUSPECT",
                     "description": f"Date d'émission dans le futur : date_emission={raw}"}]
    except ValueError:
        pass
    return []


def _r7_siret_format(fields):
    """R7 — le SIRET doit faire 14 chiffres et passer l'algo de Luhn."""
    siret = fields.get("siret")
    if not siret:
        return []
    clean = re.sub(r"\s", "", str(siret))

    if len(clean) != 14 or not clean.isdigit():
        return [{"rule": "R7", "severity": "FRAUDULEUX",
                 "description": f"SIRET format invalide (attendu 14 chiffres) : {siret}"}]

    # Luhn : on double 1 chiffre sur 2, si >9 on soustrait 9, somme % 10 == 0
    total = sum(int(d) if i % 2 else sum(divmod(int(d) * 2, 10))
                for i, d in enumerate(clean))
    if total % 10 != 0:
        return [{"rule": "R7", "severity": "FRAUDULEUX",
                 "description": f"SIRET checksum Luhn invalide : {siret}"}]
    return []


# ---------- moteur principal ----------

def detect(payload: dict) -> dict:
    """Lance toutes les règles + le ML sur le document et ses docs liés.
    Retourne le verdict avec le score d'anomalie."""
    start = time.perf_counter()
    anomalies = []

    file_id = payload.get("file_id", "unknown")
    doc_type = _resolve_type(payload.get("doc_type", ""))
    ocr_conf = payload.get("ocr_confidence", 1.0)
    classif_conf = payload.get("classification_confidence", 1.0)
    main_f = _normalize_fields(payload.get("fields", {}))
    related = payload.get("related_docs", [])

    # règles sur le doc principal (R2→R7, R1 a besoin d'un 2e doc)
    for rule_fn in [_r3_tva_taux_legal, _r4_calcul_ttc, _r5_iban_format,
                    _r6_date_emission, _r7_siret_format]:
        anomalies.extend(rule_fn(main_f))
    anomalies.extend(_r2_urssaf_expiration(doc_type, main_f))

    # détection ML (IsolationForest)
    ht = _to_float(main_f.get("montant_ht"))
    ttc = _to_float(main_f.get("montant_ttc"))
    tva = _to_float(main_f.get("tva"))
    siret = main_f.get("siret")
    anomalies.extend(check_document(ht, ttc, tva, ocr_conf,
                                    siret=str(siret) if siret else None))

    # règles sur chaque doc lié
    for rel in related:
        rt = _resolve_type(rel.get("doc_type", ""))
        rf = _normalize_fields(rel.get("fields", {}))
        anomalies.extend(_r1_siret_coherent(doc_type, main_f, rt, rf))
        anomalies.extend(_r2_urssaf_expiration(rt, rf))
        anomalies.extend(_r5_iban_format(rf))
        anomalies.extend(_r7_siret_format(rf))

    # comparaison des docs liés entre eux (ex: Kbis vs URSSAF)
    for i, a in enumerate(related):
        for b in related[i + 1:]:
            anomalies.extend(_r1_siret_coherent(
                _resolve_type(a.get("doc_type", "")), _normalize_fields(a.get("fields", {})),
                _resolve_type(b.get("doc_type", "")), _normalize_fields(b.get("fields", {}))))

    # dédoublonnage (même règle + même message = on garde qu'une fois)
    seen, unique = set(), []
    for a in anomalies:
        k = (a["rule"], a["description"])
        if k not in seen:
            seen.add(k)
            unique.append(a)
    anomalies = unique

    # score final : somme pondérée des anomalies, plafonné à 1
    score = min(1.0, round(sum(SEVERITY_WEIGHT.get(a["severity"], 0) for a in anomalies), 2))
    confidence = round(ocr_conf * classif_conf * (1 - score * 0.3), 2)

    # statut : frauduleux si au moins un high, suspect si que des medium
    has_fraud = any(a["severity"] == "FRAUDULEUX" for a in anomalies)
    status = "frauduleux" if has_fraud else ("suspect" if anomalies else "OK")

    return {
        "file_id": file_id,
        "status": status,
        "anomaly_score": score,
        "confidence_score": confidence,
        "anomalies": [{"rule": a["rule"], "description": a["description"],
                       "severity": SEVERITY_OUTPUT.get(a["severity"], a["severity"])}
                      for a in anomalies],
        "processing_time_ms": round((time.perf_counter() - start) * 1000),
    }
