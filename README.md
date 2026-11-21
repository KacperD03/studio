# Weimar Research Hub

System wyszukiwania i kojarzenia partnerów naukowych pomiędzy uczelniami **Polski, Niemiec i Francji (Trójkąt Weimarski)** ze **wszystkich dziedzin nauki**.

## Uczelnie i skala bazy
- **824 naukowców** z **9 uczelni** (`PL=271`, `DE=275`, `FR=278`) i **25 dyscyplin OpenAlex**.
- **Polska:** AGH, Uniwersytet Warszawski (UW), Politechnika Warszawska (PW).
- **Niemcy:** TU Monachium (TUM), Uniwersytet w Heidelbergu, Uniwersytet Humboldta w Berlinie.
- **Francja:** Sorbonne Université, Université Paris-Saclay, ENS.
- **4069 publikacji** (w tym **3353 abstrakty**), zapisane w JSON i SQLite (`data/weimar.db`).

## Kroki projektu (do niezależnego oddania)

| Krok | Folder | Uruchomienie / Test | Krótki opis |
| :---: | :--- | :--- | :--- |
| **1** | `krok_1_pozyskanie_danych/` | `python krok_1_pozyskanie_danych/check_data.py` | Pobranie danych z OpenAlex API i walidacja |
| **2** | `krok_2_profilowanie/` | `python krok_2_profilowanie/test_profiling.py` | Kompetencje, biogramy i embeddingi 128-D |
| **3** | `krok_3_rekomendacje/` | `python krok_3_rekomendacje/test_recommendations.py` | Podobieństwo tematyczne i komplementarność |
| **4** | `krok_4_uzasadnienia/` | `python krok_4_uzasadnienia/test_explain.py` | Uzasadnianie RAG z cytowaniem publikacji |
| **5** | `krok_5_propozycje/` | `python krok_5_propozycje/test_proposals.py` | Propozycje projektów (WP1–WP4) dla 2–3 osób |
| **6** | `krok_6_aplikacja_webowa/` | `python krok_6_aplikacja_webowa/backend/app.py` | Aplikacja webowa (`http://localhost:5000`) |
| **7** | `krok_7_eksperymenty/` | `python krok_7_eksperymenty/run_experiments.py` | 24 scenariusze, P@5, P@10, MAP i raport |

Każdy folder zawiera własny plik `README.md` z prostym sprawozdaniem i instrukcją pokazu.
