"""
Test weryfikacyjny dla KROKU 2: Profilowanie naukowców (Wszystkie Dziedziny)
Projekt: Weimar Research Hub
"""

import json
import math
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import PROFILES_FILE

def test_profiles():
    path = PROFILES_FILE
    if not path.exists():
        path = CURRENT_DIR / "researchers_profiled.json"

    if not path.exists():
        print(f"[BŁĄD] Brak pliku {path}. Uruchom najpierw: python profile_researchers.py")
        return False

    with open(path, "r", encoding="utf-8") as f:
        profiles = json.load(f)

    print("=" * 72)
    print("WERYFIKACJA PROFILOWANIA NAUKOWCÓW — KROK 2")
    print("=" * 72)
    print(f"Liczba sprofilowanych naukowców: {len(profiles)}")

    missing_comp = sum(1 for p in profiles if not p.get("competencies"))
    missing_sum = sum(1 for p in profiles if not p.get("profile_summary"))
    missing_emb = sum(1 for p in profiles if not p.get("embedding"))

    print(f"- Naukowcy z wyznaczonymi kompetencjami: {len(profiles) - missing_comp}/{len(profiles)} [OK]")
    print(f"- Naukowcy ze zsyntetyzowanym biogramem: {len(profiles) - missing_sum}/{len(profiles)} [OK]")
    print(f"- Naukowcy z wektorami semantycznymi (embeddings): {len(profiles) - missing_emb}/{len(profiles)} [OK]")

    sample = profiles[0]
    emb = sample.get("embedding", [])
    dim = len(emb)
    norm = math.sqrt(sum(x * x for x in emb))
    print(f"- Wymiar wektorów embeddings: {dim} wymiarów")
    print(f"- Norma L2 wektora testowego: {norm:.4f} (cel ~1.0) -> {'[OK]' if 0.98 <= norm <= 1.02 else '[UWAGA]'}")

    # Wyświetlamy 2 przykładowych naukowców z różnych dziedzin
    samples = [profiles[0]]
    for p in profiles[1:]:
        if p.get("primary_domain") != profiles[0].get("primary_domain") and p.get("country") != profiles[0].get("country"):
            samples.append(p)
            break

    for i, s in enumerate(samples, 1):
        print(f"\nPRZYKŁAD PROFILU #{i}:")
        print("-" * 72)
        print(f"Imię i nazwisko: {s.get('name')}")
        print(f"Afiliacja:      {s.get('affiliation')} ({s.get('country')})")
        print(f"Domena główna:  {s.get('primary_domain')} (OpenAlex: {s.get('field')})")
        print(f"Kompetencje:    {', '.join(s.get('competencies', []))}")
        print(f"Biogram:        {s.get('profile_summary')}")

    all_ok = (missing_comp == 0 and missing_sum == 0 and missing_emb == 0 and len(profiles) >= 300)
    print("\n" + "=" * 72)
    print(f"STATUS KROKU 2: {'SUKCES — PROFILOWANIE POPRAWNE [OK]' if all_ok else 'WYMAGA POPRAWY'}")
    print("=" * 72)
    return all_ok

if __name__ == "__main__":
    test_profiles()
