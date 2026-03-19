"""
F05 - Vérification cohérence inter-documents
Moteur de règles métier R1 à R7 pour détecter les anomalies
entre les documents d'un même fournisseur (facture, devis, Kbis, etc.)
"""

import re
import time
from datetime import date
from typing import Any

from ml_detector import check_document

# On mappe les types de documents reçus depuis l'API vers des noms courts
# pour simplifier les comparaisons dans le code
DOC_TYPE_MAP = {
    "FACTURE": "facture",
    "DEVIS": "devis",
    "ATTESTATION_SIRET": "siret",
    "ATTESTATION_URSSAF": "urssaf",
    "EXTRAIT_KBIS": "kbis",
    "RIB": "rib",
}

# Certains champs ont des noms différents selon le type de document
# (ex: "fournisseur" sur une facture = "nom_entreprise" sur un Kbis)
# On les normalise pour pouvoir les comparer facilement
FIELD_ALIASES = {
    "fournisseur": "nom_entreprise",
    "nom_titulaire": "nom_entreprise",
    "tva_rate": "tva",
    "date_emission": "date_emission",
    "date_expiration": "date_expiration",
}

# Les 4 taux de TVA autorisés en France
TVA_TAUX_LEGAUX = {0.0, 5.5, 10.0, 20.0}

# Poids de chaque sévérité pour calculer le score global d'anomalie
# FRAUDULEUX pèse plus lourd que SUSPECT dans le score final
SEVERITY_WEIGHT = {"FRAUDULEUX": 0.30, "SUSPECT": 0.12}

# En interne on utilise FRAUDULEUX/SUSPECT, mais en sortie JSON
# on renvoie high/medium comme demandé dans le contrat d'API
SEVERITY_OUTPUT = {"FRAUDULEUX": "high", "SUSPECT": "medium"}


# ----------------------------------------------------------------
# Fonctions utilitaires
# ----------------------------------------------------------------

def _norm(value: Any) -> str:
    """Nettoie une valeur pour la comparer : minuscule, espaces unifiés."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).lower().strip())


def _to_float(value: Any) -> float | None:
    """Convertit une valeur en float, gère les formats avec virgule ou symboles."""
    if value is None:
        return None
    try:
        return float(re.sub(r"[^\d.,\-]", "", str(value)).replace(",", "."))
    except (ValueError, TypeError):
        return None


def _normalize_fields(fields) -> dict:
    """Renomme les champs via les alias pour uniformiser les noms."""
    # Si c'est un objet Pydantic, on le convertit en dict
    if hasattr(fields, "model_dump"):
        fields = fields.model_dump()
    elif not isinstance(fields, dict):
        fields = dict(fields)
    out = {}
    for k, v in fields.items():
        out[FIELD_ALIASES.get(k, k)] = v
    # On garde aussi les clés originales au cas où
    for k, v in fields.items():
        if k not in out:
            out[k] = v
    return out


def _resolve_type(raw: str) -> str:
    """Convertit le doc_type API (ex: 'FACTURE') en type interne (ex: 'facture')."""
    return DOC_TYPE_MAP.get(raw, raw.lower())


# ----------------------------------------------------------------
# Implémentation des 7 règles métier
# Chaque fonction retourne une liste d'anomalies (vide si tout est OK)
# ----------------------------------------------------------------

def _r1_siret_coherent(main_type, main_fields, rel_type, rel_fields):
    """
    R1 - On vérifie que le SIRET est le même entre le document principal
    et chaque document lié. Si c'est pas le cas, c'est très suspect.
    """
    siret_a = main_fields.get("siret")
    siret_b = rel_fields.get("siret")
    if not siret_a or not siret_b:
        return []
    if _norm(siret_a) == _norm(siret_b):
        return []
    return [{
        "rule": "R1",
        "severity": "FRAUDULEUX",
        "description": f"SIRET incohérent : {main_type.upper()}={siret_a} / {rel_type.upper()}={siret_b}",
    }]


def _r2_urssaf_expiration(doc_type, fields):
    """
    R2 - Si le document est une attestation URSSAF, on check que
    la date d'expiration n'est pas dépassée. Un doc expiré = pas valable.
    """
    if doc_type != "urssaf":
        return []
    date_exp = fields.get("date_expiration") or fields.get("date_validite")
    if not date_exp:
        return []
    try:
        exp = date.fromisoformat(str(date_exp))
        if exp < date.today():
            return [{
                "rule": "R2",
                "severity": "FRAUDULEUX",
                "description": f"Attestation URSSAF expirée : date_expiration={date_exp} < aujourd'hui",
            }]
    except ValueError:
        pass
    return []


def _r3_tva_taux_legal(fields):
    """
    R3 - Le taux de TVA doit être un des taux légaux français.
    Si on trouve un taux bizarre (genre 15%), c'est louche.
    """
    tva = _to_float(fields.get("tva"))
    if tva is None:
        return []
    if tva not in TVA_TAUX_LEGAUX:
        return [{
            "rule": "R3",
            "severity": "SUSPECT",
            "description": f"Taux de TVA non légal : {tva}% (attendu : 0%, 5.5%, 10% ou 20%)",
        }]
    return []


def _r4_calcul_ttc(fields):
    """
    R4 - On recalcule le TTC à partir du HT et du taux de TVA,
    et on compare avec le TTC annoncé. Tolérance de 0.02€ pour
    les arrondis, au-delà c'est une incohérence.
    """
    ht = _to_float(fields.get("montant_ht"))
    ttc = _to_float(fields.get("montant_ttc"))
    tva = _to_float(fields.get("tva"))
    if ht is None or ttc is None or tva is None:
        return []
    expected = round(ht * (1 + tva / 100), 2)
    ecart = abs(expected - ttc)
    if ecart > 0.02:
        return [{
            "rule": "R4",
            "severity": "SUSPECT",
            "description": f"Calcul TTC incohérent : HT={ht} + TVA {tva}% = {expected}, mais TTC={ttc} (écart={ecart:.2f}€)",
        }]
    return []


def _r5_iban_format(fields):
    """
    R5 - Validation de l'IBAN : pour un IBAN français, il doit faire
    27 caractères et passer le check modulo 97 (norme ISO 13616).
    """
    iban = fields.get("iban")
    if not iban:
        return []
    iban_clean = re.sub(r"\s", "", str(iban)).upper()

    # Un IBAN français fait toujours 27 caractères
    if iban_clean.startswith("FR") and len(iban_clean) != 27:
        return [{
            "rule": "R5",
            "severity": "SUSPECT",
            "description": f"IBAN format invalide : longueur={len(iban_clean)} (attendu 27 pour FR) : {iban}",
        }]

    # Vérif du format général (2 lettres + 2 chiffres + reste alphanum)
    if not re.match(r"^[A-Z]{2}\d{2}[A-Z0-9]+$", iban_clean):
        return [{
            "rule": "R5",
            "severity": "SUSPECT",
            "description": f"IBAN format invalide : {iban}",
        }]

    # Vérification du checksum : on déplace les 4 premiers chars à la fin,
    # on convertit les lettres en chiffres (A=10, B=11...) et on fait modulo 97
    rearranged = iban_clean[4:] + iban_clean[:4]
    numeric = "".join(str(ord(c) - 55) if c.isalpha() else c for c in rearranged)
    if int(numeric) % 97 != 1:
        return [{
            "rule": "R5",
            "severity": "SUSPECT",
            "description": f"IBAN checksum invalide (modulo 97) : {iban}",
        }]
    return []


def _r6_date_emission(fields):
    """
    R6 - La date d'émission d'un document ne peut pas être dans le futur.
    Si c'est le cas, le document a probablement été falsifié.
    """
    date_em = fields.get("date_emission")
    if not date_em:
        return []
    try:
        em = date.fromisoformat(str(date_em))
        if em > date.today():
            return [{
                "rule": "R6",
                "severity": "SUSPECT",
                "description": f"Date d'émission dans le futur : date_emission={date_em}",
            }]
    except ValueError:
        pass
    return []


def _r7_siret_format(fields):
    """
    R7 - Le SIRET doit faire exactement 14 chiffres et passer
    l'algorithme de Luhn (même principe que pour les cartes bancaires).
    """
    siret = fields.get("siret")
    if not siret:
        return []
    siret_clean = re.sub(r"\s", "", str(siret))

    # Check de la longueur et que c'est bien que des chiffres
    if len(siret_clean) != 14 or not siret_clean.isdigit():
        return [{
            "rule": "R7",
            "severity": "FRAUDULEUX",
            "description": f"SIRET format invalide (attendu 14 chiffres) : {siret}",
        }]

    # Algorithme de Luhn : on double un chiffre sur deux,
    # si le résultat dépasse 9 on soustrait 9, et la somme totale
    # doit être divisible par 10
    total = sum(
        int(d) if i % 2 else sum(divmod(int(d) * 2, 10))
        for i, d in enumerate(siret_clean)
    )
    if total % 10 != 0:
        return [{
            "rule": "R7",
            "severity": "FRAUDULEUX",
            "description": f"SIRET checksum Luhn invalide : {siret}",
        }]
    return []


# ----------------------------------------------------------------
# Moteur principal : orchestre toutes les règles
# ----------------------------------------------------------------

def detect(payload: dict) -> dict:
    """
    Point d'entrée du moteur. Reçoit le payload JSON du webservice,
    applique les 7 règles sur le doc principal + les docs liés,
    et retourne le résultat formaté.
    """
    start = time.perf_counter()
    anomalies = []

    # Extraction des infos du payload
    file_id = payload.get("file_id", "unknown")
    doc_type = _resolve_type(payload.get("doc_type", ""))
    ocr_confidence = payload.get("ocr_confidence", 1.0)
    classif_confidence = payload.get("classification_confidence", 1.0)
    main_fields = _normalize_fields(payload.get("fields", {}))
    related_docs = payload.get("related_docs", [])

    # On applique d'abord les règles sur le document principal
    # (R2 à R7, R1 nécessite un 2e document pour comparer)
    anomalies.extend(_r2_urssaf_expiration(doc_type, main_fields))
    anomalies.extend(_r3_tva_taux_legal(main_fields))
    anomalies.extend(_r4_calcul_ttc(main_fields))
    anomalies.extend(_r5_iban_format(main_fields))
    anomalies.extend(_r6_date_emission(main_fields))
    anomalies.extend(_r7_siret_format(main_fields))

    # Règle ML
    montant_ht = _to_float(main_fields.get("montant_ht"))
    montant_ttc = _to_float(main_fields.get("montant_ttc"))
    tva = _to_float(main_fields.get("tva"))
    siret = main_fields.get("siret")
    anomalies.extend(check_document(montant_ht, montant_ttc, tva, ocr_confidence, siret=str(siret) if siret else None))

    # Ensuite on traite chaque document lié
    for rel in related_docs:
        rel_type = _resolve_type(rel.get("doc_type", ""))
        rel_fields = _normalize_fields(rel.get("fields", {}))

        anomalies.extend(_r1_siret_coherent(doc_type, main_fields, rel_type, rel_fields))
        anomalies.extend(_r2_urssaf_expiration(rel_type, rel_fields))
        anomalies.extend(_r5_iban_format(rel_fields))
        anomalies.extend(_r7_siret_format(rel_fields))

    # On compare aussi les related_docs entre eux
    for i, rel_a in enumerate(related_docs):
        for rel_b in related_docs[i + 1:]:
            type_a = _resolve_type(rel_a.get("doc_type", ""))
            type_b = _resolve_type(rel_b.get("doc_type", ""))
            fields_a = _normalize_fields(rel_a.get("fields", {}))
            fields_b = _normalize_fields(rel_b.get("fields", {}))
            anomalies.extend(_r1_siret_coherent(type_a, fields_a, type_b, fields_b))

    # Dédoublonnage
    seen = set()
    unique = []
    for a in anomalies:
        key = (a["rule"], a["description"])
        if key not in seen:
            seen.add(key)
            unique.append(a)
    anomalies = unique

    # Calcul du score d'anomalie (entre 0 et 1)
    anomaly_score = min(1.0, round(
        sum(SEVERITY_WEIGHT.get(a["severity"], 0) for a in anomalies), 2
    ))

    # Score de confiance global
    confidence_score = round(
        ocr_confidence * classif_confidence * (1 - anomaly_score * 0.3), 2
    )

    has_frauduleux = any(a["severity"] == "FRAUDULEUX" for a in anomalies)
    if has_frauduleux:
        status = "frauduleux"
    elif anomalies:
        status = "suspect"
    else:
        status = "OK"

    output_anomalies = [
        {
            "rule": a["rule"],
            "description": a["description"],
            "severity": SEVERITY_OUTPUT.get(a["severity"], a["severity"]),
        }
        for a in anomalies
    ]

    elapsed_ms = round((time.perf_counter() - start) * 1000)

    return {
        "file_id": file_id,
        "status": status,
        "anomaly_score": anomaly_score,
        "confidence_score": confidence_score,
        "anomalies": output_anomalies,
        "processing_time_ms": elapsed_ms,
    }
