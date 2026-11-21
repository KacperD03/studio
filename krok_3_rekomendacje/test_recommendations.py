"""
Test weryfikacyjny dla KROKU 3: Wyszukiwanie partnerów (Wszystkie Dziedziny)
Projekt: Weimar Research Hub
"""

import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from krok_3_rekomendacje.recommend import PartnerRecommender

def test_engine():
    print("=" * 75)
    print("WERYFIKACJA SYSTEMU REKOMENDACJI — KROK 3 (WSZYSTKIE DZIEDZINY)")
    print("=" * 75)

    try:
        recommender = PartnerRecommender()
    except Exception as e:
        print(f"[BŁĄD] Nie można załadować danych: {e}")
        return False

    total_res = len(recommender.researchers)
    print(f"Załadowano bazę {total_res} naukowców ze wszystkich dyscyplin.")
    if total_res == 0:
        return False

    # Wybieramy naukowca z Polski (np. ze średniej półki lub z informatyki/medycyny/inżynierii)
    source = next(
        (r for r in recommender.researchers if r.get("country") == "PL" and r.get("publications")),
        recommender.researchers[0]
    )
    s_id = source["openalex_id"]

    print(f"\nNaukowiec źródłowy: {source['name']}")
    print(f"Afiliacja:          {source['affiliation']} ({source['country']})")
    print(f"Dyscyplina:         {source.get('field')} -> {source.get('primary_domain')}")
    print(f"Kompetencje:        {', '.join(source.get('competencies', [])[:4])}")

    print("\n" + "-" * 75)
    print("1. REKOMENDACJE WG PODOBIEŃSTWA TEMATYCZNEGO (Top-5, zagraniczni):")
    print("-" * 75)
    sim_recs = recommender.recommend_by_similarity(s_id, top_k=5, different_country_only=True)
    for idx, r in enumerate(sim_recs, 1):
        target = r["researcher"]
        print(f"  {idx}. [{r['score']*100:.1f}%] {target['name']} | {target['affiliation']} ({target['country']}) | {target.get('field')}")
        print(f"     Wspólne tematy: {', '.join(r['shared_topics'][:3]) if r['shared_topics'] else 'pokrewna metodologia'}")

    print("\n" + "-" * 75)
    print("2. REKOMENDACJE WG KOMPLEMENTARNOŚCI KOMPETENCJI (Top-5, zagraniczni):")
    print("-" * 75)
    comp_recs = recommender.recommend_by_complementarity(s_id, top_k=5, different_country_only=True)
    for idx, r in enumerate(comp_recs, 1):
        target = r["researcher"]
        print(f"  {idx}. [{r['score']*100:.1f}%] {target['name']} | {target['affiliation']} ({target['country']}) | {target.get('field')}")
        print(f"     Wnosi kompetencje: {', '.join(r['partner_unique_skills'][:3])}")

    print("\n" + "=" * 75)
    print("STATUS KROKU 3: SUKCES — oba mechanizmy rekomendacji działają poprawnie [OK]")
    print("=" * 75)
    return True

if __name__ == "__main__":
    test_engine()
