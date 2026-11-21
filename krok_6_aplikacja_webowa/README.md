# Krok 6: Aplikacja webowa (Demonstrator)

## Co zostało zrobione
- **Backend REST API (`backend/app.py` w Flask + alternatywnie `backend/main_fastapi.py` w FastAPI):**
  - `/api/researchers` — wyszukiwanie, sortowanie oraz filtrowanie po kraju, uczelni, obszarze i dyscyplinie OpenAlex,
  - `/api/researchers/<id>` — pełny profil badacza z biogramem i abstraktami,
  - `/api/recommendations` — rankingi podobieństwa i komplementarności,
  - `/api/explain` — uzasadnienia RAG z cytowaniem prac,
  - `/api/proposals` — generator projektów dla 2–3 osób,
  - `/api/stats` — statystyki 824 naukowców, 4069 publikacji i 25 dyscyplin.
- **Frontend (`frontend/index.html` w React 18 + Tailwind CSS):**
  - Katalog z paginacją, dynamicznymi filtrami dziedzinowymi i sortowaniem,
  - Silnik rekomendacji z przełącznikiem trybów i rozwijanymi uzasadnieniami RAG,
  - Generator konsorcjum (z szybkim losowaniem PL–DE–FR i eksportem do `.md`),
  - Zakładka statystyk bazy.

## Jak uruchomić i pokazać
```bash
python krok_6_aplikacja_webowa/backend/app.py
```
Otwórz w przeglądarce: **`http://localhost:5000`**.

Przy oddawaniu pokaż filtrowanie po dyscyplinie i kraju, kartę naukowca z abstraktami, przełączenie trybu rekomendacji z uzasadnieniem RAG oraz wygenerowanie i pobranie projektu `.md` dla konsorcjum PL–DE–FR.
