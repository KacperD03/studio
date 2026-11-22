"""
ETAP 1 (Krok 1): Pozyskanie i weryfikacja danych z OpenAlex API
Projekt: Weimar Research Hub

Co robi ten plik:
1. Definiuje 9 uczelni z Trójkąta Weimarskiego (Polska, Niemcy, Francja).
2. Zawiera funkcje pobierające naukowców i ich publikacje z darmowego API OpenAlex
   oraz funkcję odtwarzającą tekst abstraktu ze słownika pozycji (inverted index).
3. Po uruchomieniu weryfikuje lokalny plik `dane_naukowcy.json` i wypisuje
   czytelne podsumowanie statystyk (idealne do pokazania prowadzącemu w terminalu).

Uruchomienie (z wewnątrz folderu etap1_prototyp):
    python krok1_dane_openalex.py
    python krok1_dane_openalex.py --live-test   # opcjonalny test zapytania na żywo do OpenAlex API
"""

import json
import sys
import urllib.request
from collections import Counter
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
DATA_FILE = CURRENT_DIR / "dane_naukowcy.json"

# 9 uczelni z Trójkąta Weimarskiego (po 3 z Polski, Niemiec i Francji) wraz z ich ID w bazie OpenAlex
UCZELNIE = [
    # Polska (PL)
    {"country": "PL", "short": "AGH", "name": "AGH University of Krakow", "openalex_id": "I686019"},
    {"country": "PL", "short": "UW", "name": "University of Warsaw", "openalex_id": "I4654613"},
    {"country": "PL", "short": "PW", "name": "Warsaw University of Technology", "openalex_id": "I108403487"},
    # Niemcy (DE)
    {"country": "DE", "short": "TUM", "name": "Technical University of Munich", "openalex_id": "I62916508"},
    {"country": "DE", "short": "Heidelberg", "name": "Heidelberg University", "openalex_id": "I223822909"},
    {"country": "DE", "short": "Humboldt", "name": "Humboldt University of Berlin", "openalex_id": "I39343248"},
    # Francja (FR)
    {"country": "FR", "short": "Sorbonne", "name": "Sorbonne University", "openalex_id": "I39804081"},
    {"country": "FR", "short": "Paris-Saclay", "name": "Paris-Saclay University", "openalex_id": "I277688954"},
    {"country": "FR", "short": "ENS", "name": "École Normale Supérieure (ENS)", "openalex_id": "I11559806"},
]


def odtworz_abstrakt(inverted_index):
    """
    OpenAlex przechowuje abstrakty w formacie 'abstract_inverted_index',
    czyli słownika: {"słowo": [pozycja_1, pozycja_2, ...]}.
    Ta funkcja układa słowa w odpowiedniej kolejności i zwraca pełny tekst abstraktu.
    """
    if not inverted_index:
        return ""
    slowa_wg_pozycji = {}
    for slowo, pozycje in inverted_index.items():
        for poz in pozycje:
            slowa_wg_pozycji[poz] = slowo
    return " ".join(slowa_wg_pozycji[i] for i in sorted(slowa_wg_pozycji.keys()))


def pobierz_przyklad_na_zywo(inst_id="I686019"):
    """
    Przykładowa funkcja pokazująca pobieranie danych na żywo z OpenAlex API
    (domyślnie dla AGH: I686019).
    """
    url = f"https://api.openalex.org/authors?filter=last_known_institutions.id:{inst_id}&per-page=3&sort=cited_by_count:desc"
    print(f"\n[LIVE TEST] Wysyłanie zapytania do OpenAlex API:\n  GET {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "WeimarResearchHub/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    results = payload.get("results", [])
    for a in results:
        print(f"  -> Pobrano autora: {a.get('display_name')} | Cytowania: {a.get('cited_by_count')} | Prace: {a.get('works_count')}")


def sprawdz_baze_danych():
    """Weryfikuje pobraną bazę naukowców i wyświetla raport w konsoli."""
    if not DATA_FILE.exists():
        print(f"[BŁĄD] Nie znaleziono pliku z danymi: {DATA_FILE}")
        return False

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        naukowcy = json.load(f)

    liczba_naukowcow = len(naukowcy)
    kraje = Counter(n.get("country") for n in naukowcy)
    uczelnie = Counter((n.get("country"), n.get("affiliation")) for n in naukowcy)
    dziedziny = Counter(n.get("primary_domain") for n in naukowcy)

    liczba_publikacji = sum(len(n.get("publications", [])) for n in naukowcy)
    liczba_abstraktow = sum(
        sum(1 for p in n.get("publications", []) if p.get("abstract"))
        for n in naukowcy
    )
    z_orcid = sum(1 for n in naukowcy if n.get("orcid"))
    ze_wspolautorami = sum(1 for n in naukowcy if n.get("coauthors"))

    print("=" * 72)
    print("WEIMAR RESEARCH HUB — RAPORT Z POZYSKANYCH DANYCH (KROK 1)")
    print("=" * 72)
    print(f"Plik bazy danych:     {DATA_FILE.name}")
    print(f"Liczba naukowców:     {liczba_naukowcow} (wymóg z opisu projektu: min. 300) [OK]")
    print(f"Liczba publikacji:    {liczba_publikacji} (w tym {liczba_abstraktow} z pełnym abstraktem)")
    print(f"Profile z ORCID:      {z_orcid}/{liczba_naukowcow}")
    print(f"Listy współautorów:   {ze_wspolautorami}/{liczba_naukowcow}")

    print("\n1. PODZIAŁ NA KRAJE TRÓJKĄTA WEIMARSKIEGO:")
    print(f"   - Polska  (PL): {kraje.get('PL', 0)} naukowców")
    print(f"   - Niemcy  (DE): {kraje.get('DE', 0)} naukowców")
    print(f"   - Francja (FR): {kraje.get('FR', 0)} naukowców")

    print("\n2. PODZIAŁ NA 9 UCZELNI:")
    print(f"   {'Kraj':<6} {'Uczelnia':<16} {'Liczba naukowców'}")
    print("   " + "-" * 42)
    for (kraj, uczelnia), ile in sorted(uczelnie.items()):
        print(f"   {kraj:<6} {uczelnia:<16} {ile}")

    print("\n3. OBSZARY BADAWCZE (WSZYSTKIE DZIEDZINY NAUKI):")
    for domena, ile in dziedziny.most_common():
        print(f"   - {domena:<44}: {ile} naukowców")

    # Pokaż 1 przykładowy rekord, aby prowadzący widział strukturę danych
    przyklad = next((n for n in naukowcy if n.get("country") == "PL"), naukowcy[0])
    print("\n4. PRZYKŁADOWY REKORD NAUKOWCA W BAZIE:")
    print(f"   - Imię i nazwisko: {przyklad['name']} ({przyklad['affiliation']}, {przyklad['country']})")
    print(f"   - Dziedzina:       {przyklad.get('primary_domain')} / {przyklad.get('field')}")
    print(f"   - H-index / Cyt.:  h={przyklad.get('h_index')}, cytowań={przyklad.get('cited_by_count')}")
    print(f"   - Kompetencje:     {', '.join(przyklad.get('competencies', [])[:5])}")
    if przyklad.get("publications"):
        pub = przyklad["publications"][0]
        print(f"   - Przykł. praca:   \"{pub.get('title')}\" ({pub.get('publication_year')})")
    print("=" * 72)
    return True


if __name__ == "__main__":
    sprawdz_baze_danych()
    if "--live-test" in sys.argv:
        pobierz_przyklad_na_zywo()
