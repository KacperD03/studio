"""
Test weryfikacyjny dla KROKU 4: Uzasadnianie rekomendacji (RAG)
Projekt: Weimar Research Hub
"""

import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from krok_3_rekomendacje.recommend import PartnerRecommender
from krok_4_uzasadnienia.explain import RecommendationExplainer

def test_explain_module():
    print("=" * 75)
    print("WERYFIKACJA SYSTEMU UZASADNIANIA REKOMENDACJI (RAG) — KROK 4")
    print("=" * 75)

    try:
        recommender = PartnerRecommender()
        explainer = RecommendationExplainer()
    except Exception as e:
        print(f"[BŁĄD] Nie można załadować modułów: {e}")
        return False

    researchers = list(explainer.by_id.values())
    if len(researchers) < 2:
        print("[BŁĄD] Zbyt mało naukowców.")
        return False

    # Wybieramy naukowca z Polski i szukamy najlepszego komplementarnego partnera z DE/FR
    source = next((r for r in researchers if r.get("country") == "PL" and r.get("publications")), researchers[0])
    recs = recommender.recommend_by_complementarity(source["openalex_id"], top_k=1, different_country_only=True)
    target = recs[0]["researcher"] if recs else researchers[1]

    print(f"Para dobrana do uzasadnienia:")
    print(f"1. {source['name']} ({source['affiliation']}, {source['country']}) — {source.get('field')}")
    print(f"2. {target['name']} ({target['affiliation']}, {target['country']}) — {target.get('field')}")

    explanation = explainer.explain_recommendation(source["openalex_id"], target["openalex_id"], rec_type="complementarity")

    print("\n" + "-" * 75)
    print("WYGENEROWANE UZASADNIENIE RAG:")
    print("-" * 75)
    print(explanation["detailed_explanation"])
    print("-" * 75)

    pub_a = explanation["researcher_a"]["cited_publication"]["title"]
    pub_b = explanation["researcher_b"]["cited_publication"]["title"]
    print(f"\nCytowana publikacja A: {pub_a} [OK]")
    print(f"Cytowana publikacja B: {pub_b} [OK]")
    print(f"Wykryte słowa kluczowe styku: {', '.join(explanation['shared_keywords'])}")

    success = bool(pub_a) and bool(pub_b) and len(explanation["detailed_explanation"]) > 100
    print("\n" + "=" * 75)
    print(f"STATUS KROKU 4: {'SUKCES — UZASADNIENIE Z PUBLIKACJAMI POPRAWNE [OK]' if success else 'BŁĄD'}")
    print("=" * 75)
    return success

if __name__ == "__main__":
    test_explain_module()
