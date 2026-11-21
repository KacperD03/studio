# Krok 4: Uzasadnianie rekomendacji (RAG)

## Co zostało zrobione
- Zaimplementowano moduł `RecommendationExplainer` (`explain.py`) realizujący mechanizm **RAG (Retrieval-Augmented Generation)**.
- Dla wskazanej pary naukowców skrypt analizuje tytuły i abstrakty ich publikacji, dobiera dwie najbardziej powiązane prace i wyznacza wspólne słowa kluczowe styku (z odfiltrowaniem słów ogólnych).
- Generuje czytelne uzasadnienie po polsku z **bezpośrednimi cytatami konkretnych publikacji** (tytuł, rok, fragment abstraktu), z opcją rozszerzenia przez OpenAI API (`OPENAI_API_KEY`).

## Jak uruchomić i pokazać
```bash
python krok_4_uzasadnienia/test_explain.py
```

Przy oddawaniu uruchom `test_explain.py` i wskaż w wygenerowanym opisie konkretne tytuły publikacji, lata wydania, cytowane fragmenty abstraktów oraz słowa kluczowe styku.
