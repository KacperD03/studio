# Krok 2: Profilowanie naukowców

## Co zostało zrobione
- Zmapowano dorobek każdego naukowca do **9 głównych obszarów naukowych** oraz zachowano szczegółową dyscyplinę OpenAlex (`field`, `subfield`).
- Automatycznie wyznaczono **kluczowe kompetencje** badawcze (z odfiltrowaniem pustych słów ogólnych) oraz wygenerowano **syntetyczny biogram** w języku polskim.
- Zbudowano **128-wymiarowe wektory semantyczne (embeddings)** metodą **TF-IDF + Truncated SVD** (znormalizowane L2 do normy 1.0) na podstawie biogramu, tematów, tytułów i abstraktów (z opcją użycia `SentenceTransformer` przez `USE_SENTENCE_TRANSFORMERS=1`).
- Zapisano profile do `data/researchers_profiled.json` i bazy SQLite `data/weimar.db` (schemat PostgreSQL w `database/schema.sql`).

## Wynik weryfikacji
- **824/824** naukowców ma wyznaczone kompetencje, biogram i wektor 128-D (norma L2 = `1.0000`).
- Baza `data/weimar.db` przechowuje **824 naukowców** oraz **4069 publikacji**.

## Jak uruchomić i pokazać
```bash
python krok_2_profilowanie/test_profiling.py
```
*(Przeliczenie profili od nowa: `python krok_2_profilowanie/profile_researchers.py`.)*

Przy oddawaniu uruchom `test_profiling.py` i pokaż przykładowe biogramy, kompetencje oraz poprawność wektorów 128-D.
