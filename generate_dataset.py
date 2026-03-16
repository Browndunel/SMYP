"""
Script principal de génération du dataset synthétique de documents administratifs français.

Usage :
    python generate_dataset.py

Ou en important la fonction :
    from generate_dataset import generate_dataset
    generate_dataset(n_per_type=20, seed=42)
"""
from __future__ import annotations

import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path

# Compatibilité import relatif quand lancé directement
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
from pdf2image import convert_from_bytes
from tqdm import tqdm

from generators import (
    generate_attestation_urssaf,
    generate_devis,
    generate_facture,
    generate_kbis,
    generate_rib,
)
from utils.degradation import degrade_image

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
    team_names: list[str],
    out_raw: Path,
    out_scans: Path,
    out_gt: Path,
    dpi: int = 150,
) -> dict:
    """
    Génère un document complet :
      PDF → PNG source → PNG dégradés (un par niveau) → JSON ground truth.

    Returns:
        Dictionnaire de résumé pour dataset_summary.json.
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
    pages = convert_from_bytes(pdf_bytes, dpi=dpi)
    source_img = pages[0]

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
        "anomalies": ground_truth["anomalies"],
        "fichier_pdf": pdf_path.name,
        "fichier_gt": gt_path.name,
    }


# ---------------------------------------------------------------------------
# Fonction principale
# ---------------------------------------------------------------------------

def generate_dataset(
    output_dir: str | Path = "dataset",
    n_per_type: int = 20,
    scenario_distribution: dict[str, float] | None = None,
    degradation_levels: list[str] | None = None,
    team_names: list[str] | None = None,
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
        team_names:             Prénoms/noms de l'équipe pour personnaliser.
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
    if team_names is None:
        team_names = []

    # Validation
    total_weight = sum(scenario_distribution.values())
    if abs(total_weight - 1.0) > 0.01:
        raise ValueError(
            f"La distribution des scénarios doit sommer à 1.0 (actuel : {total_weight:.3f})"
        )

    # Initialisation des graines
    random.seed(seed)
    np.random.seed(seed)

    # Création de l'arborescence
    output_dir = Path(output_dir)
    out_raw = output_dir / "raw"
    out_scans = output_dir / "scans"
    out_gt = output_dir / "ground_truth"
    for d in (out_raw, out_scans, out_gt):
        d.mkdir(parents=True, exist_ok=True)

    print(f"\nDataset generator — {n_per_type} docs/type × {len(_GENERATORS)} types = "
          f"{n_per_type * len(_GENERATORS)} documents\n")

    rng = random.Random(seed)
    summary_entries = []
    stats: dict[str, dict] = {t: {"total": 0, "coherent": 0, "incoherent": 0} for t in _GENERATORS}

    total = n_per_type * len(_GENERATORS)
    with tqdm(total=total, unit="doc", colour="cyan") as pbar:
        for doc_type in _GENERATORS:
            for _ in range(n_per_type):
                scenario = _weighted_scenario_sample(scenario_distribution, rng)
                pbar.set_description(f"{doc_type:20s} [{scenario}]")

                try:
                    entry = _process_document(
                        doc_type=doc_type,
                        scenario=scenario,
                        degradation_levels=degradation_levels,
                        team_names=team_names,
                        out_raw=out_raw,
                        out_scans=out_scans,
                        out_gt=out_gt,
                        dpi=dpi,
                    )
                    summary_entries.append(entry)
                    stats[doc_type]["total"] += 1
                    if entry["coherent"]:
                        stats[doc_type]["coherent"] += 1
                    else:
                        stats[doc_type]["incoherent"] += 1

                except Exception as exc:  # noqa: BLE001
                    tqdm.write(f"[ERREUR] {doc_type}/{scenario} : {exc}")

                pbar.update(1)

    # Fichier récapitulatif
    dataset_summary = {
        "generated_at": datetime.now().isoformat(),
        "seed": seed,
        "n_per_type": n_per_type,
        "total_documents": len(summary_entries),
        "scenario_distribution": scenario_distribution,
        "degradation_levels": degradation_levels,
        "team_names": team_names,
        "stats_par_type": stats,
        "documents": summary_entries,
    }
    summary_path = output_dir / "dataset_summary.json"
    summary_path.write_text(
        json.dumps(dataset_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Rapport final
    print(f"\n{'='*60}")
    print(f"  Dataset genere dans : {output_dir.resolve()}")
    print(f"  Documents total     : {len(summary_entries)}")
    print(f"  Coherents           : {sum(e['coherent'] for e in summary_entries)}")
    print(f"  Incoherents         : {sum(not e['coherent'] for e in summary_entries)}")
    print(f"\n  Par type :")
    for t, s in stats.items():
        print(f"    {t:22s} total={s['total']:3d}  OK={s['coherent']:3d}  KO={s['incoherent']:3d}")
    print(f"\n  Recapitulatif : {summary_path.resolve()}")
    print(f"{'='*60}\n")

    return output_dir


# ---------------------------------------------------------------------------
# Point d'entrée CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    generate_dataset(
        output_dir="dataset",
        n_per_type=20,
        scenario_distribution={
            "normal": 0.50,
            "siret_incoherent": 0.15,
            "date_expiree": 0.15,
            "tva_incoherente": 0.10,
            "falsifie": 0.10,
        },
        degradation_levels=["low", "medium", "high"],
        team_names=["Alice Martin", "Bob Dupont", "Claire Moreau", "David Leroy"],
        seed=42,
    )
