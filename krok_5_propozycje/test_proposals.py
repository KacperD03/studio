"""
Test weryfikacyjny dla KROKU 5: Generowanie propozycji współpracy (Wszystkie Dziedziny)
Projekt: Weimar Research Hub
"""

import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from krok_5_propozycje.generate_proposals import ProposalGenerator

def test_proposal_generation():
    print("=" * 75)
    print("WERYFIKACJA GENEROWANIA PROPOZYCJI WSPÓŁPRACY — KROK 5")
    print("=" * 75)

    try:
        gen = ProposalGenerator()
    except Exception as e:
        print(f"[BŁĄD] Nie można załadować modułu: {e}")
        return False

    researchers = list(gen.by_id.values())
    if len(researchers) < 3:
        return False

    # Dobieramy 3 naukowców z różnych krajów (PL, DE, FR) i różnych domen (np. AI + Medycyna + Inżynieria/Fizyka)
    r_pl = next((r for r in researchers if r.get("country") == "PL" and "Informatyka" in r.get("primary_domain", "")), researchers[0])
    r_de = next((r for r in researchers if r.get("country") == "DE" and "Medycyna" in r.get("primary_domain", "")), researchers[1])
    r_fr = next((r for r in researchers if r.get("country") == "FR" and r.get("primary_domain") not in {r_pl.get("primary_domain"), r_de.get("primary_domain")}), researchers[2])

    test_ids = [r_pl["openalex_id"], r_de["openalex_id"], r_fr["openalex_id"]]

    print("Wybrane interdyscyplinarne konsorcjum (Trójkąt Weimarski):")
    print(f"1. [PL] {r_pl['name']} ({r_pl['affiliation']}) — {r_pl.get('field')}")
    print(f"2. [DE] {r_de['name']} ({r_de['affiliation']}) — {r_de.get('field')}")
    print(f"3. [FR] {r_fr['name']} ({r_fr['affiliation']}) — {r_fr.get('field')}")

    proposal = gen.generate_proposal(test_ids)

    print("\n" + "-" * 75)
    print(f"TYTUŁ PROJEKTU:   {proposal['project_title']}")
    print(f"AKRONIM PROJEKTU: {proposal['acronym']}")
    print("-" * 75)

    print("\n1. UZASADNIENIE NAUKOWE:")
    print(proposal["scientific_rationale"])

    print("\n2. PAKIETY ROBOCZE I PODZIAŁ KOMPETENCJI:")
    for wp in proposal["work_packages"]:
        print(f"   [{wp['wp_id']}] {wp['nazwa']} (Lider: {wp['lider']})")
        for task in wp["zadania"]:
            print(f"       - {task}")

    print("\n3. OCZEKIWANE REZULTATY:")
    for key, val in proposal["expected_outcomes"].items():
        if isinstance(val, list):
            print(f"   * {key.upper()}:")
            for it in val:
                print(f"       • {it}")
        else:
            print(f"   * {key.upper()}: {val}")

    ok = bool(proposal.get("project_title")) and len(proposal.get("competency_division", {})) == 3
    print("\n" + "=" * 75)
    print(f"STATUS KROKU 5: {'SUKCES — PROPOZYCJA WYGENEROWANA POPRAWNIE [OK]' if ok else 'BŁĄD'}")
    print("=" * 75)
    return ok

if __name__ == "__main__":
    test_proposal_generation()
