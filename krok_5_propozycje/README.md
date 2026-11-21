# Krok 5: Generowanie propozycji współpracy

## Co zostało zrobione
- Zaimplementowano moduł `ProposalGenerator` (`generate_proposals.py`) tworzący kompletny projekt badawczy dla **2–3 wybranych naukowców** (np. konsorcjum PL–DE–FR).
- Generator tworzy:
  - Interdyscyplinarny **tytuł i akronim projektu** (`WEIMAR-...`),
  - **Uzasadnienie naukowe** łączące kompetencje partnerów,
  - **Pakiety robocze (`WP1`–`WP4`)** z imiennym przypisaniem liderów, ich kompetencji i konkretnych publikacji,
  - **Oczekiwane rezultaty** (publikacje Q1, otwarte artefakty, wnioski grantowe **Horizon Europe / NCN–DFG–ANR**).

## Jak uruchomić i pokazać
```bash
python krok_5_propozycje/test_proposals.py
```

Przy oddawaniu uruchom `test_proposals.py` i pokaż gotowy szkielet wniosku dla trójstronnego konsorcjum z różnych dziedzin nauki.
