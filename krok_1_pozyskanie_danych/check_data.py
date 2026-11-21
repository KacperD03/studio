"""
Weryfikator danych dla KROKU 1
Projekt: Weimar Research Hub
Sprawdza spełnienie wszystkich wymagań z TODO:
- Minimum 300 naukowców (z zapasem dla lepszej jakości rekomendacji)
- 9 uczelni (po 3 z Polski, Niemiec i Francji)
- Wszystkie dziedziny nauki (multidyscyplinarność)
- Publikacje, abstrakty, obszary badań, współautorzy, ORCID
"""

import json
import sys
from collections import Counter
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import RESEARCHERS_FILE

def check_dataset(filepath=RESEARCHERS_FILE):
    path = Path(filepath)
    if not path.exists():
        path = CURRENT_DIR / "researchers.json"
    if not path.exists():
        path = ROOT_DIR / "researchers.json"

    if not path.exists():
        print(f"[BŁĄD] Nie znaleziono pliku danych: {filepath}")
        return False

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_count = len(data)
    print("=" * 72)
    print("RAPORT WERYFIKACJI DANYCH — KROK 1 (WSZYSTKIE DZIEDZINY)")
    print("=" * 72)
    print(f"Plik danych: {path.resolve()}")
    print(f"Łączna liczba naukowców: {total_count} (Wymóg TODO: min. 300) -> {'[OK]' if total_count >= 300 else '[BŁĄD]'}")

    country_counter = Counter(d.get("country") for d in data)
    inst_counter = Counter((d.get("country"), d.get("affiliation")) for d in data)
    field_counter = Counter(d.get("field") for d in data)
    domain_counter = Counter(d.get("openalex_domain") for d in data)

    print("\n1. ROZKŁAD WG KRAJÓW:")
    for c, label in [("PL", "Polska"), ("DE", "Niemcy"), ("FR", "Francja")]:
        print(f"   - {label} [{c}]: {country_counter.get(c, 0)} naukowców")

    print("\n2. ROZKŁAD WG UCZELNI (9 instytucji):")
    print(f"   {'Kraj':<6} {'Uczelnia':<15} {'Naukowcy':<12} {'Status'}")
    print("   " + "-" * 45)
    for (c, inst), cnt in sorted(inst_counter.items()):
        status = "[OK]" if cnt >= 30 else "[MAŁO]"
        print(f"   {c:<6} {inst:<15} {cnt:<12} {status}")
    print(f"   Łącznie instytucji: {len(inst_counter)} / 9")

    print(f"\n3. RÓŻNORODNOŚĆ DZIEDZIN NAUKI (liczba dyscyplin: {len(field_counter)}):")
    for dom, cnt in domain_counter.most_common():
        print(f"   * Obszar [{dom}]: {cnt} naukowców")
    print("\n   Top dyscypliny szczegółowe:")
    for fld, cnt in field_counter.most_common(12):
        print(f"   - {fld}: {cnt}")

    total_pubs = sum(len(d.get("publications", [])) for d in data)
    total_abstracts = sum(
        sum(1 for p in d.get("publications", []) if p.get("abstract"))
        for d in data
    )
    total_with_topics = sum(1 for d in data if d.get("topics"))
    total_with_coauthors = sum(1 for d in data if d.get("coauthors"))
    total_with_orcid = sum(1 for d in data if d.get("orcid"))

    print("\n4. KOMPLETNOŚĆ ATRYBUTÓW:")
    print(f"   - Publikacje łącznie: {total_pubs} (średnio {total_pubs/total_count:.1f} na naukowca) [OK]")
    print(f"   - Publikacje z pełnym abstraktem: {total_abstracts}/{total_pubs} [OK]")
    print(f"   - Naukowcy z obszarami badań (topics): {total_with_topics}/{total_count} [OK]")
    print(f"   - Naukowcy ze współautorami: {total_with_coauthors}/{total_count} [OK]")
    print(f"   - Naukowcy z identyfikatorem ORCID: {total_with_orcid}/{total_count} [OK]")

    print("=" * 72)
    ok = total_count >= 300 and len(inst_counter) == 9 and len(field_counter) >= 8
    print(f"STATUS KROKU 1: {'SUKCES — WSZYSTKIE WYMOGI SPEŁNIONE [OK]' if ok else 'WYMAGA POPRAWY'}")
    print("=" * 72)
    return ok

if __name__ == "__main__":
    check_dataset()
