# ============================================================
# SMYP – Lancement scénario E2E
# Usage : python tests/e2e/run_scenario.py --scenario E01
# ============================================================

import argparse
import os
import sys
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL  = "http://localhost:5000"
AIRFLOW_URL  = "http://localhost:8080"
AIRFLOW_USER = os.getenv("AIRFLOW_USERNAME", "admin")
AIRFLOW_PASS = os.getenv("AIRFLOW_PASSWORD", "smypadmin")

SCENARIOS = {
    "E01": {
        "description": "Pipeline nominal — facture propre",
        "file":        "dataset/output/test_fixtures/facture_yoni_sas_propre.pdf",
        "expected_status": "OK"
    },
    "E02": {
        "description": "OCR scan flou",
        "file":        "dataset/output/test_fixtures/facture_scan_flou.png",
        "expected_status": "OK"
    },
    "E03": {
        "description": "OCR rotation 15 degrés",
        "file":        "dataset/output/test_fixtures/facture_rotated_15.jpg",
        "expected_status": "OK"
    },
    "E04": {
        "description": "SIRET incohérent → frauduleux",
        "file":        "dataset/output/test_fixtures/facture_siret_mismatch.pdf",
        "expected_status": "frauduleux"
    },
    "E05": {
        "description": "URSSAF expirée → frauduleux",
        "file":        "dataset/output/test_fixtures/attestation_urssaf_expiree.pdf",
        "expected_status": "frauduleux"
    },
    "E06": {
        "description": "TVA 15% → suspect",
        "file":        "dataset/output/test_fixtures/facture_tva_15pct.pdf",
        "expected_status": "suspect"
    },
}

def run_scenario(scenario_id: str):
    scenario = SCENARIOS.get(scenario_id)
    if not scenario:
        print(f"[E2E] Scénario inconnu : {scenario_id}")
        print(f"[E2E] Scénarios disponibles : {list(SCENARIOS.keys())}")
        sys.exit(1)

    print(f"\n[E2E] ── Scénario {scenario_id} ──────────────────────")
    print(f"[E2E] {scenario['description']}")

    # Vérifie que le fichier existe
    file_path = scenario["file"]
    if not os.path.exists(file_path):
        print(f"[E2E] ✗ Fichier manquant : {file_path}")
        print(f"[E2E] Lance d'abord : python dataset/generate.py")
        sys.exit(1)

    # Upload le fichier
    print(f"[E2E] Upload : {file_path}")
    with open(file_path, "rb") as f:
        response = requests.post(
            f"{BACKEND_URL}/api/upload",
            files={"files": (os.path.basename(file_path), f)},
            timeout=30
        )

    if response.status_code not in [200, 202]:
        print(f"[E2E] ✗ Upload échoué : {response.status_code} — {response.text}")
        sys.exit(1)

    result   = response.json()
    file_id  = result.get("file_ids", [None])[0]
    print(f"[E2E] ✓ Upload réussi — file_id={file_id}")

    # Poll le statut jusqu'à completion (max 120s)
    print(f"[E2E] Attente pipeline...")
    max_wait = 120
    waited   = 0
    while waited < max_wait:
        time.sleep(5)
        waited += 5
        status_r = requests.get(
            f"{BACKEND_URL}/api/documents/{file_id}",
            timeout=10
        )
        if status_r.status_code == 200:
            doc = status_r.json()
            pipeline_status = doc.get("pipeline_status", "")
            doc_status      = doc.get("status", "")

            print(f"[E2E] [{waited}s] pipeline={pipeline_status} | doc={doc_status}")

            if pipeline_status == "success":
                # Vérifie le statut attendu
                if doc_status == scenario["expected_status"]:
                    print(f"[E2E] ✓ SUCCÈS — statut={doc_status} (attendu={scenario['expected_status']})")
                    return True
                else:
                    print(f"[E2E] ✗ ÉCHEC — statut={doc_status} (attendu={scenario['expected_status']})")
                    return False
            elif pipeline_status == "failed":
                print(f"[E2E] ✗ Pipeline en échec")
                return False

    print(f"[E2E] ✗ Timeout après {max_wait}s")
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lance un scénario E2E SMYP")
    parser.add_argument("--scenario", required=True, help="Ex: E01, E02, E03...")
    parser.add_argument("--all",      action="store_true", help="Lance tous les scénarios")
    args = parser.parse_args()

    if args.all:
        results = {}
        for sid in SCENARIOS:
            results[sid] = run_scenario(sid)
        print("\n[E2E] ── RÉSUMÉ ──────────────────────────────")
        for sid, ok in results.items():
            status = "✓ PASS" if ok else "✗ FAIL"
            print(f"[E2E] {status} — {sid} : {SCENARIOS[sid]['description']}")
        total  = len(results)
        passed = sum(1 for v in results.values() if v)
        print(f"\n[E2E] {passed}/{total} scénarios réussis\n")
    else:
        success = run_scenario(args.scenario)
        sys.exit(0 if success else 1)