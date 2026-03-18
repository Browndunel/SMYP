"""
Script principal de génération du dataset synthétique de documents administratifs français.

Usage :
    python generate_dataset.py

Ou en important la fonction :
    from generate_dataset import generate_dataset
    generate_dataset(n_per_type=20, seed=42)
"""
from __future__ import annotations

import csv
import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Compatibilité import relatif quand lancé directement
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pypdfium2 as pdfium
from tqdm import tqdm

from generators import (
    generate_attestation_urssaf,
    generate_devis,
    generate_facture,
    generate_kbis,
    generate_rib,
)
from utils.degradation import degrade_image, degrade_image_smartphone
from utils.faker_helpers import TEAM_COMPANIES

# ---------------------------------------------------------------------------
# Types et scénarios disponibles
# ---------------------------------------------------------------------------

_GENERATORS = {
    "facture": generate_facture,
    "devis": generate_devis,
    "attestation_urssaf": generate_attestation_urssaf,
    "kbis": generate_kbis,
    "rib": generate_rib,
}

_ALL_SCENARIOS = ["normal", "siret_incoherent", "date_expiree", "tva_incoherente", "falsifie"]

# Certains scénarios ne s'appliquent pas à tous les types.
# On mappe vers le scénario le plus proche si nécessaire.
_SCENARIO_COMPAT = {
    "rib": {
        "siret_incoherent": "falsifie",
        "date_expiree": "normal",
        "tva_incoherente": "normal",
    },
    "kbis": {
        "date_expiree": "normal",
        "tva_incoherente": "normal",
    },
}


_SCENARIOS_CATALOG: list[dict] = [
    {
        "id": "normal",
        "description": "Document cohérent, aucune anomalie",
        "anomaly_codes": [],
        "affected_fields": [],
        "compatibility": {t: "native" for t in _GENERATORS},
    },
    {
        "id": "siret_incoherent",
        "description": "SIRET affiché sur le document ≠ SIRET réel de l'entreprise",
        "anomaly_codes": ["SIRET_INCOHERENT"],
        "affected_fields": ["fournisseur.siret"],
        "compatibility": {
            "facture": "native", "devis": "native",
            "attestation_urssaf": "native", "kbis": "native",
            "rib": "fallback→falsifie",
        },
    },
    {
        "id": "date_expiree",
        "description": "Date de validité/expiration dans le passé",
        "anomaly_codes": ["DATE_EXPIREE"],
        "affected_fields": ["date_echeance"],
        "compatibility": {
            "facture": "fallback→normal", "devis": "native",
            "attestation_urssaf": "native", "kbis": "fallback→normal",
            "rib": "fallback→normal",
        },
    },
    {
        "id": "tva_incoherente",
        "description": "Montant TVA ne correspondant pas au taux légal de 20 %",
        "anomaly_codes": ["TVA_INCOHERENTE"],
        "affected_fields": ["tva_montant", "montant_ttc"],
        "compatibility": {
            "facture": "native", "devis": "native",
            "attestation_urssaf": "fallback→normal", "kbis": "fallback→normal",
            "rib": "fallback→normal",
        },
    },
    {
        "id": "falsifie",
        "description": "Cumul des anomalies supportées par le type de document",
        "anomaly_codes": ["SIRET_INCOHERENT", "TVA_INCOHERENTE", "DATE_EXPIREE", "IBAN_INCOHERENT"],
        "affected_fields": ["fournisseur.siret", "tva_montant", "montant_ttc", "date_echeance"],
        "compatibility": {t: "native" for t in _GENERATORS},
        "note": "Anomalies effectives : facture→SIRET+TVA, devis→SIRET+TVA+DATE, attestation→SIRET+DATE, kbis→SIRET, rib→IBAN",
    },
]


def _resolve_scenario(doc_type: str, scenario: str) -> str:
    """Adapte le scénario si non supporté par le type de document."""
    compat = _SCENARIO_COMPAT.get(doc_type, {})
    return compat.get(scenario, scenario)


def _weighted_scenario_sample(
    distribution: dict[str, float],
    rng: random.Random,
) -> str:
    """Tire un scénario selon la distribution fournie."""
    scenarios = list(distribution.keys())
    weights = [distribution[s] for s in scenarios]
    return rng.choices(scenarios, weights=weights, k=1)[0]


# ---------------------------------------------------------------------------
# Pipeline document
# ---------------------------------------------------------------------------

def _process_document(
    doc_type: str,
    scenario: str,
    degradation_levels: list[str],
    team_names: list[str] | None,
    out_raw: Path,
    out_scans: Path,
    out_gt: Path,
    dpi: int = 150,
) -> dict:
    """
    Génère un document complet :
      PDF → PNG source → PNG dégradés (un par niveau) → JSON ground truth.

    Returns:
        Dictionnaire de résumé pour dataset_summary.json et labels.csv.
    """
    resolved_scenario = _resolve_scenario(doc_type, scenario)
    generator = _GENERATORS[doc_type]

    # 1. Génération PDF
    pdf_bytes, ground_truth = generator(
        scenario=resolved_scenario,
        team_names=team_names,
    )

    doc_id = ground_truth["id"]
    short_id = doc_id[:8]
    base_name = f"{doc_type}_{resolved_scenario}_{short_id}"

    # 2. Sauvegarde PDF
    pdf_path = out_raw / f"{base_name}.pdf"
    pdf_path.write_bytes(pdf_bytes)

    # 3. Conversion PDF → PIL image (première page)
    pdf_doc = pdfium.PdfDocument(pdf_bytes)
    page = pdf_doc[0]
    bitmap = page.render(scale=dpi / 72)
    source_img = bitmap.to_pil()

    # 4. Sauvegarde PNG source (scan "parfait")
    source_png_path = out_scans / f"{base_name}_original.png"
    source_img.save(source_png_path, format="PNG")

    # 5. Versions dégradées
    scan_files = {}
    for level in degradation_levels:
        degraded = degrade_image(source_img, level=level)
        scan_path = out_scans / f"{base_name}_{level}.png"
        degraded.save(scan_path, format="PNG")
        scan_files[level] = scan_path.name

    # 5b. Version smartphone
    smartphone_img = degrade_image_smartphone(source_img)
    smartphone_path = out_scans / f"{base_name}_smartphone.jpg"
    smartphone_img.save(smartphone_path, format="JPEG", quality=85)
    scan_files["smartphone"] = smartphone_path.name

    # 6. Ground truth enrichi
    ground_truth["fichiers"] = {
        "pdf": pdf_path.name,
        "png_original": source_png_path.name,
        "png_scans": scan_files,
    }
    gt_path = out_gt / f"{base_name}.json"
    gt_path.write_text(
        json.dumps(ground_truth, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "id": doc_id,
        "type": doc_type,
        "scenario": resolved_scenario,
        "coherent": ground_truth["coherent"],
        "is_fraud": not ground_truth["coherent"],
        "anomalies": ground_truth["anomalies"],
        "expected_siret": ground_truth["fournisseur"]["siret"],
        "montant_ttc": ground_truth.get("montant_ttc", 0.0),
        "tva_rate": ground_truth.get("tva_taux", 0),
        "date_expiration": ground_truth.get("date_echeance", ""),
        "fichier_pdf": pdf_path.name,
        "fichier_gt": gt_path.name,
    }


# ---------------------------------------------------------------------------
# Helpers CSV / stats
# ---------------------------------------------------------------------------

def _write_scenarios_json(
    output_dir: Path,
    scenario_distribution: dict[str, float],
    generated_at: str,
) -> None:
    """Écrit scenarios.json dans output_dir."""
    payload = {
        "generated_at": generated_at,
        "doc_types": list(_GENERATORS.keys()),
        "scenario_distribution_used": scenario_distribution,
        "scenarios": _SCENARIOS_CATALOG,
    }
    (output_dir / "scenarios.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _write_labels_csv(output_dir: Path, entries: list[dict]) -> None:
    """Écrit labels.csv dans output_dir (une ligne par document)."""
    fieldnames = [
        "file_name", "doc_type", "is_fraud", "anomaly_type",
        "expected_siret", "montant_ttc", "tva_rate",
        "date_expiration", "degradation_level",
    ]
    csv_path = output_dir / "labels.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for e in entries:
            writer.writerow({
                "file_name": e["fichier_pdf"],
                "doc_type": e["type"],
                "is_fraud": e["is_fraud"],
                "anomaly_type": "|".join(e["anomalies"]) if e["anomalies"] else "",
                "expected_siret": e["expected_siret"],
                "montant_ttc": e["montant_ttc"],
                "tva_rate": e["tva_rate"],
                "date_expiration": e["date_expiration"],
                "degradation_level": "none",
            })


def _compute_stats(entries: list[dict]) -> dict[str, dict]:
    """Calcule les stats par type pour un ensemble d'entrées."""
    stats: dict[str, dict] = {t: {"total": 0, "coherent": 0, "incoherent": 0} for t in _GENERATORS}
    for e in entries:
        t = e["type"]
        stats[t]["total"] += 1
        if e["coherent"]:
            stats[t]["coherent"] += 1
        else:
            stats[t]["incoherent"] += 1
    return stats


# ---------------------------------------------------------------------------
# Fonction principale
# ---------------------------------------------------------------------------

def generate_dataset(
    output_dir: str | Path = "generated_dataset",
    n_per_type: int = 20,
    scenario_distribution: dict[str, float] | None = None,
    degradation_levels: list[str] | None = None,
    team_names: list[str] | None = None,
    split: dict[str, float] | None = None,
    seed: int = 42,
    dpi: int = 150,
) -> Path:
    """
    Génère un dataset synthétique de documents administratifs français.

    Args:
        output_dir:             Répertoire de sortie (sera créé si absent).
        n_per_type:             Nombre de documents générés par type.
        scenario_distribution:  Distribution des scénarios (somme = 1).
        degradation_levels:     Niveaux de dégradation à appliquer.
        team_names:             Noms complets de sociétés équipe (scénario S8).
                                Quand fourni, 6 docs par type (30 total) utilisent
                                ces noms avec scénario normal.
        split:                  Ratio train/test, ex : {"train": 0.70, "test": 0.30}.
                                Split stratifié par (type, scénario).
                                Si None, structure à plat (comportement par défaut).
        seed:                   Graine aléatoire pour la reproductibilité.
        dpi:                    Résolution de conversion PDF → PNG.

    Returns:
        Chemin du répertoire dataset créé.
    """
    if scenario_distribution is None:
        scenario_distribution = {
            "normal": 0.50,
            "siret_incoherent": 0.15,
            "date_expiree": 0.15,
            "tva_incoherente": 0.10,
            "falsifie": 0.10,
        }
    if degradation_levels is None:
        degradation_levels = ["low", "medium", "high"]

    # Validation
    total_weight = sum(scenario_distribution.values())
    if abs(total_weight - 1.0) > 0.01:
        raise ValueError(
            f"La distribution des scénarios doit sommer à 1.0 (actuel : {total_weight:.3f})"
        )
    if split is not None:
        split_total = sum(split.values())
        if abs(split_total - 1.0) > 0.01:
            raise ValueError(
                f"Le split doit sommer à 1.0 (actuel : {split_total:.3f})"
            )

    # Initialisation des graines
    random.seed(seed)
    np.random.seed(seed)
    rng = random.Random(seed)

    output_dir = Path(output_dir)

    # ---------------------------------------------------------------------------
    # Phase 1 : Planification des assignments (doc_type, scenario, team_names)
    # ---------------------------------------------------------------------------

    # 6 docs équipe par type quand team_names est fourni (30 total sur 100)
    team_per_type = 6 if team_names else 0

    plan: list[dict] = []
    for doc_type in _GENERATORS:
        for i in range(n_per_type):
            is_team = i < team_per_type
            if is_team:
                plan.append({
                    "doc_type": doc_type,
                    "scenario": "normal",
                    "team_names": team_names,
                })
            else:
                scenario = _weighted_scenario_sample(scenario_distribution, rng)
                plan.append({
                    "doc_type": doc_type,
                    "scenario": scenario,
                    "team_names": None,
                })

    # ---------------------------------------------------------------------------
    # Phase 2 : Split stratifié (si demandé)
    # ---------------------------------------------------------------------------

    train_set: set[int] = set()
    if split is not None:
        train_ratio = split.get("train", 0.70)
        groups: dict[tuple, list[int]] = defaultdict(list)
        for idx, p in enumerate(plan):
            resolved = _resolve_scenario(p["doc_type"], p["scenario"])
            groups[(p["doc_type"], resolved)].append(idx)

        split_rng = random.Random(seed + 1)
        for indices in groups.values():
            shuffled = list(indices)
            split_rng.shuffle(shuffled)
            n_train = math.floor(len(shuffled) * train_ratio)
            train_set.update(shuffled[:n_train])

    # ---------------------------------------------------------------------------
    # Phase 3 : Création de l'arborescence
    # ---------------------------------------------------------------------------

    if split is not None:
        for subset in ("train", "test"):
            for sub in ("raw", "scans", "ground_truth"):
                (output_dir / subset / sub).mkdir(parents=True, exist_ok=True)
    else:
        for sub in ("raw", "scans", "ground_truth"):
            (output_dir / sub).mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------------------
    # Phase 4 : Génération
    # ---------------------------------------------------------------------------

    total = len(plan)
    print(f"\nDataset generator — {n_per_type} docs/type × {len(_GENERATORS)} types = "
          f"{total} documents\n")

    all_entries: list[dict] = []
    train_entries: list[dict] = []
    test_entries: list[dict] = []

    with tqdm(total=total, unit="doc", colour="cyan") as pbar:
        for idx, p in enumerate(plan):
            doc_type = p["doc_type"]
            scenario = p["scenario"]
            tn = p["team_names"]

            if split is not None:
                subset = "train" if idx in train_set else "test"
                out_raw = output_dir / subset / "raw"
                out_scans = output_dir / subset / "scans"
                out_gt = output_dir / subset / "ground_truth"
            else:
                out_raw = output_dir / "raw"
                out_scans = output_dir / "scans"
                out_gt = output_dir / "ground_truth"

            pbar.set_description(f"{doc_type:20s} [{scenario}]")

            try:
                entry = _process_document(
                    doc_type=doc_type,
                    scenario=scenario,
                    degradation_levels=degradation_levels,
                    team_names=tn,
                    out_raw=out_raw,
                    out_scans=out_scans,
                    out_gt=out_gt,
                    dpi=dpi,
                )
                all_entries.append(entry)
                if split is not None:
                    if idx in train_set:
                        train_entries.append(entry)
                    else:
                        test_entries.append(entry)

            except Exception as exc:  # noqa: BLE001
                tqdm.write(f"[ERREUR] {doc_type}/{scenario} : {exc}")

            pbar.update(1)

    # ---------------------------------------------------------------------------
    # Phase 5 : labels.csv
    # ---------------------------------------------------------------------------

    _write_labels_csv(output_dir, all_entries)
    if split is not None:
        _write_labels_csv(output_dir / "train", train_entries)
        _write_labels_csv(output_dir / "test", test_entries)

    # ---------------------------------------------------------------------------
    # Phase 6 : dataset_summary.json
    # ---------------------------------------------------------------------------

    generated_at = datetime.now().isoformat()
    _write_scenarios_json(output_dir, scenario_distribution, generated_at)

    overall_stats = _compute_stats(all_entries)
    dataset_summary: dict = {
        "generated_at": generated_at,
        "seed": seed,
        "n_per_type": n_per_type,
        "total_documents": len(all_entries),
        "scenario_distribution": scenario_distribution,
        "degradation_levels": degradation_levels,
        "team_names": team_names or [],
        "stats_par_type": overall_stats,
        "documents": all_entries,
    }

    if split is not None:
        dataset_summary["split"] = split
        dataset_summary["stats_train"] = _compute_stats(train_entries)
        dataset_summary["stats_test"] = _compute_stats(test_entries)
        dataset_summary["n_train"] = len(train_entries)
        dataset_summary["n_test"] = len(test_entries)

    summary_path = output_dir / "dataset_summary.json"
    summary_path.write_text(
        json.dumps(dataset_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # ---------------------------------------------------------------------------
    # Rapport final
    # ---------------------------------------------------------------------------

    print(f"\n{'='*60}")
    print(f"  Dataset genere dans : {output_dir.resolve()}")
    print(f"  Documents total     : {len(all_entries)}")
    print(f"  Coherents           : {sum(e['coherent'] for e in all_entries)}")
    print(f"  Incoherents         : {sum(not e['coherent'] for e in all_entries)}")
    if split is not None:
        print(f"  Train               : {len(train_entries)}")
        print(f"  Test                : {len(test_entries)}")
    print(f"\n  Par type :")
    for t, s in overall_stats.items():
        print(f"    {t:22s} total={s['total']:3d}  OK={s['coherent']:3d}  KO={s['incoherent']:3d}")
    print(f"\n  Recapitulatif : {summary_path.resolve()}")
    print(f"{'='*60}\n")

    return output_dir


# ---------------------------------------------------------------------------
# Point d'entrée CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    generate_dataset(
        output_dir="generated_dataset",
        n_per_type=20,
        scenario_distribution={
            "normal": 0.50,
            "siret_incoherent": 0.15,
            "date_expiree": 0.15,
            "tva_incoherente": 0.10,
            "falsifie": 0.10,
        },
        degradation_levels=["low", "medium", "high"],
        team_names=TEAM_COMPANIES,
        split={"train": 0.70, "test": 0.30},
        seed=42,
    )
