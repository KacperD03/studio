# Krok 7: Eksperymenty i raport końcowy

## Co zostało zrobione
- Przygotowano skrypt `run_experiments.py` przeprowadzający ewaluację na **24 scenariuszach testowych** (12 dyscyplin OpenAlex w trybach podobieństwa i komplementarności dla PL, DE i FR; w zestawieniu z niezależnym baseline'em losowym).
- Obliczono metryki **Precision@5**, **Precision@10** oraz **MAP@10**, a także oceniono jakość **10 propozycji projektowych** (skala 1–5: spójność, podział ról, innowacyjność, wykonalność).
- Wygenerowano wyniki do CSV (`wyniki_eksperymentow.csv`) i krótki raport końcowy (`raport_eksperymenty.md`).

## Główne wyniki
- **Podobieństwo tematyczne (12 scen.):** P@5 = **98.3%**, P@10 = **95.0%**, MAP@10 = **98.2%**.
- **Komplementarność kompetencji (12 scen.):** P@5 = **78.3%**, P@10 = **79.2%**, MAP@10 = **83.6%**.
- **Średnia systemu (24 scen.):** P@5 = **88.3%**, P@10 = **87.1%**, MAP@10 = **90.9%** (vs **30.0%** baseline losowy).
- **Jakość propozycji współpracy (10 konsorcjów):** **4.87 / 5.00**.

## Jak uruchomić i pokazać
```bash
python krok_7_eksperymenty/run_experiments.py
```

Przy oddawaniu uruchom `run_experiments.py` i pokaż wygenerowany raport `krok_7_eksperymenty/raport_eksperymenty.md` z tabelami wyników i wnioskami.
