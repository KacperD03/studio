# Krok 3: Wyszukiwanie partnerów (Rekomendacje)

## Co zostało zrobione
Zaimplementowano dwa niezależne tryby rekomendacji w klasie `PartnerRecommender` (`recommend.py`):
1. **Podobieństwo tematyczne (`recommend_by_similarity`):**
   - Wyszukuje naukowców o zbliżonej tematyce badawczej na podstawie cosinusa wektorów 128-D oraz indeksu Jaccarda tematów.
2. **Komplementarność kompetencji (`recommend_by_complementarity`):**
   - Łączy badaczy z uzupełniających się dziedzin (macierz synergii `INTERDISCIPLINARY_SYNERGY` + kara za ten sam `field`), promując unikalne umiejętności wnoszone do zespołu i umiarkowane podobieństwo pomostowe.
- Oba tryby obsługują filtrację po kraju oraz przełącznik partnerów zagranicznych (`different_country_only=True`).

## Jak uruchomić i pokazać
```bash
python krok_3_rekomendacje/test_recommendations.py
```

Przy oddawaniu uruchom `test_recommendations.py` i pokaż na przykładzie wybranego naukowca, że pierwszy ranking dobiera specjalistów z tej samej dziedziny, a drugi dobiera partnerów z dziedzin uzupełniających.
