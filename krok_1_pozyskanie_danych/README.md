# Krok 1: Pozyskanie danych

## Co zostało zrobione
- Pobrano dane badaczy ze **wszystkich dziedzin nauki** z API **OpenAlex** dla 9 uczelni Polski, Niemiec i Francji (12 głównych dyscyplin badawczych per uczelnia).
- Zapisano dane osobowe, afiliacje, identyfikatory **ORCID**, listy publikacji z odtworzonymi abstraktami, tematy (Topics) oraz listy współautorów.
- Wynik zapisano do `data/researchers.json` oraz `krok_1_pozyskanie_danych/researchers.json`.

## Wynik weryfikacji
- **824 naukowców** (`PL: 271`, `DE: 275`, `FR: 278`) — po 81–103 badaczy na uczelnię.
- **25 dyscyplin OpenAlex** w 4 głównych domenach (m.in. Fizyka, Medycyna, Biologia, Chemia, Inżynieria, Informatyka, Materiały, Środowisko, Ekonomia, Nauki Społeczne).
- **4069 publikacji** (w tym **3353 z abstraktami**), **824/824** z tematami, **809/824** ze współautorami, **750/824** z ORCID.

## Jak uruchomić i pokazać
```bash
python krok_1_pozyskanie_danych/check_data.py
```
*(Opcjonalnie ponowne pobranie z OpenAlex: `python krok_1_pozyskanie_danych/fetch_researchers.py`.)*

Przy oddawaniu uruchom `check_data.py` i pokaż podsumowanie liczbowe krajów, uczelni, dyscyplin i abstraktów.
