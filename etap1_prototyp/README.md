# Weimar Research Hub — Prototyp Etapu 1 (Folder na pokaz)

Ten folder (`etap1_prototyp`) zawiera **samowystarczalną pierwszą część projektu** przygotowaną specjalnie na pokaz postępów prac.

> **Ważne:** Wszystko w tym folderze działa **w 100% niezależnie** od reszty repozytorium. Możecie otworzyć w VS Code / terminalu **tylko ten jeden folder** (albo nawet skopiować sam ten folder na pendrive'a / innego laptopa) i wszystko zadziała od razu.

---

## 1. Co znajduje się w tym folderze?

| Plik | Do czego służy (w jednym zdaniu) |
| :--- | :--- |
| `dane_naukowcy.json` | Gotowa, pobrana z OpenAlex baza **824 naukowców** z **9 uczelni (PL, DE, FR)** wraz z publikacjami, abstraktami i wektorami 128-D. |
| `krok1_dane_openalex.py` | Skrypt pobierający dane z OpenAlex API oraz wypisujący w terminalu raport statystyczny z zebranej bazy. |
| `krok2_profilowanie_i_rekomendacje.py` | Logika profilowania oraz **dwa algorytmy rekomendacji** (podobieństwo tematyczne i komplementarność kompetencji). |
| `app.py` | Bardzo prosty serwer **Flask** (~100 linijek), który łączy bazę i silnik rekomendacji z przeglądarką. |
| `templates/index.html` | Prosty, czytelny interfejs webowy (HTML + JS + Tailwind) do filtrowania naukowców, podglądu profili i testowania rekomendacji. |
| `requirements.txt` | Tylko 4 podstawowe biblioteki (`flask`, `numpy`, `scipy`, `requests`). |

---

## 2. Jak to uruchomić? (Tylko z tego folderu!)

Otwórz terminal, wejdź **bezpośrednio do tego folderu** i wykonaj:

```bash
cd etap1_prototyp
pip install -r requirements.txt
```

### A) Szybki pokaz w terminalu (opcjonalnie przed włączeniem strony):
1. **Raport z pobranej bazy danych (Krok 1):**
   ```bash
   python krok1_dane_openalex.py
   ```
2. **Test profilowania i rekomendacji w konsoli (Krok 2 i 3):**
   ```bash
   python krok2_profilowanie_i_rekomendacje.py
   ```

### B) Uruchomienie prostego interfejsu webowego (główny punkt pokazu):
```bash
python app.py
```
Po uruchomieniu otwórz w przeglądarce:
👉 **`http://localhost:5050`**

---

## 3. Scenariusz pokazu dla prowadzącego (krok po kroku — 3 minuty)

1. **Pokazanie bazy danych (Krok 1):**
   - Odpal w terminalu `python krok1_dane_openalex.py` lub pokaż górny pasek w przeglądarce (`http://localhost:5050`).
   - Powiedz: *"Pobraliśmy z darmowego API OpenAlex dane **824 naukowców** z **9 uczelni Trójkąta Weimarskiego** — po 3 z Polski (AGH, UW, PW), Niemiec (TUM, Heidelberg, Humboldt) i Francji (Sorbonne, Paris-Saclay, ENS). Mamy ponad **4000 publikacji** i ponad **3300 odtworzonych abstraktów** ze wszystkich dziedzin nauki."*
2. **Filtrowanie i profil naukowca (Krok 2):**
   - W przeglądarce ustaw filtr **Kraj: Polska (PL)** i **Uczelnia: AGH**, kliknij **Filtruj bazę**, a potem kliknij dowolnego naukowca na liście po lewej.
   - Powiedz: *"Na podstawie tytułów, tematów i abstraktów publikacji automatycznie wyznaczyliśmy dla każdego naukowca jego główny obszar nauki, słowa kluczowe (kompetencje), krótki opis profilu oraz 128-wymiarowy wektor semantyczny (embedding TF-IDF + SVD)."*
   - Kliknij *"Pokaż pobrane publikacje i abstrakty z OpenAlex"*, żeby prowadzący zobaczył prawdziwe artykuły naukowe.
3. **Dwa tryby rekomendacji partnerów (Krok 3):**
   - W środkowym panelu po prawej pokaż dwa przyciski trybów:
     - **Tryb 1: Podobieństwo tematyczne** — *"Tutaj liczymy podobieństwo cosinusowe (Cosine Similarity) między wektorami 128-D publikacji oraz część wspólną tematów (Indeks Jaccarda). System dobiera partnerów z Niemiec i Francji pracujących nad bardzo zbliżonym problemem w tej samej dziedzinie."*
     - **Tryb 2: Komplementarność kompetencji** — *"Po przełączeniu na drugi tryb system szuka współpracy interdyscyplinarnej — łączy uzupełniające się dziedziny (np. Informatykę/AI z Medycyną albo Fizykę z Inżynierią Materiałową), które mają wspólny punkt styku w badaniach, ale partner wnosi nowe, unikalne kompetencje."*
4. **Co planujemy robić dalej (Etap 2):**
   - Wskaż dolną żółtą ramkę **"Planowane w kolejnym etapie projektu (Etap 2 — TODO)"** na stronie.
   - Powiedz: *"Mamy już działający rdzeń: bazę z OpenAlex, profilowanie, wektory, oba silniki rekomendacji i prosty interfejs roboczy. W kolejnym etapie dokładamy: (1) moduł RAG/LLM generujący szczegółowe uzasadnienia z cytowaniem konkretnych artykułów, (2) generator propozycji wspólnych projektów dla konsorcjum 2–3 badaczy, (3) pełną bazę relacyjną oraz (4) eksperymenty ewaluacyjne z metrykami Precision@5 i Precision@10."*

---

## 4. Ściąga dla Ciebie i kolegi — jak to dokładnie działa w kodzie?

Żebyście czuli się pewnie przy pytaniach prowadzącego, oto proste wyjaśnienie każdego elementu:

### Skąd są dane i jak rozwiązaliśmy problem abstraktów w OpenAlex? (`krok1_dane_openalex.py`)
- OpenAlex API jest darmowe i nie wymaga klucza API. Pobieramy autorów po ID uczelni (`last_known_institutions.id`), a potem ich najnowsze publikacje z endpointu `/works`.
- **Ciekawostka techniczna (warto wspomnieć prowadzącemu!):** OpenAlex z powodów licencyjnych nie zwraca abstraktu jako zwykłego tekstu, tylko jako `abstract_inverted_index` — słownik `{"słowo": [pozycja_0, pozycja_5, ...]}`. Nasza funkcja `odtworz_abstrakt()` w `krok1_dane_openalex.py` składa te pozycje z powrotem w pełny tekst abstraktu.

### Jak działa profilowanie i wektory (embeddings)? (`krok2_profilowanie_i_rekomendacje.py`)
- Dla każdego naukowca łączymy tytuły jego prac, odtworzone abstrakty oraz tematy z OpenAlex.
- Z tekstu wyciągamy najczęstsze terminy naukowe (kompetencje) i przypisujemy naukowca do jednej z 9 głównych dziedzin nauki.
- Tworzymy reprezentację wektorową (**embedding 128-D**) metodą **TF-IDF + Truncated SVD (LSA)** i normalizujemy każdy wektor do długości `1.0` (dzięki temu iloczyn skalarny dwóch wektorów `A @ B` to od razu **Cosine Similarity**!).

### Jak liczymy oba rodzaje rekomendacji? (`krok2_profilowanie_i_rekomendacje.py`)
1. **Tryb 1 — Podobieństwo tematyczne (`rekomenduj_podobnych`):**
   - `60%` * Cosine Similarity wektorów 128-D + `25%` * Indeks Jaccarda wspólnych tematów i kompetencji + `15%` * bonus za tę samą dyscyplinę naukową.
   - Im wyższy wynik, tym bardziej bliźniaczy profil badawczy.
2. **Tryb 2 — Komplementarność kompetencji (`rekomenduj_komplementarnych`):**
   - Chcemy połączyć badaczy z **różnych, ale uzupełniających się dziedzin** (np. AI + Medycyna, Chemia + Inżynieria).
   - `50%` * Waga synergii między dziedzinami (z tabeli `SYNERGIA_DZIEDZIN`; ta sama wąska dyscyplina dostaje niską wagę `0.20`, a uzupełniające się dziedziny ok. `0.90–0.96`).
   - `32%` * *Bridge Score* (funkcja Gaussa wokół `Cosine Similarity = 0.30`) — szukamy par, które mają **umiarkowany punkt styku** (np. wspólny obiekt badań lub metoda), ale nie dublują się w 100%.
   - `18%` * Odsetek **nowych, unikalnych kompetencji**, które partner wnosi do zespołu.

---

## 5. Podział: Co już mamy (Etap 1) vs Co zostało do zrobienia (Etap 2)

### Zrobione na jutro (Etap 1):
- [x] **Zadanie 1 (Pozyskanie danych):** Pobrano 824 naukowców (wymóg min. 300) z 9 uczelni (PL, DE, FR) i >4000 publikacji z OpenAlex API.
- [x] **Zadanie 2 (Profilowanie):** Wyznaczenie dziedzin, kompetencji, biogramów oraz wektorów semantycznych 128-D.
- [x] **Zadanie 3 (Wyszukiwanie partnerów):** Zaimplementowane oba tryby rekomendacji (podobieństwo tematyczne + komplementarność kompetencji) z filtrem międzynarodowym.
- [x] **Wstępny interfejs (MVP do Zadania 6):** Prosta aplikacja Flask + HTML/JS pozwalająca przeglądać bazę i testować rekomendacje na żywo.

### Zostaje do zrobienia w przyszłości (Etap 2):
- [ ] **Zadanie 4 (Uzasadnianie rekomendacji RAG / LLM):** Rozbudowa uzasadnień o automatyczne cytowanie konkretnych artykułów i abstraktów obu naukowców.
- [ ] **Zadanie 5 (Generowanie propozycji współpracy):** Moduł generujący dla wybranych 2–3 naukowców wspólny temat projektu, podział pakietów roboczych (WP) i oczekiwane rezultaty.
- [ ] **Zadanie 6 (Rozbudowa aplikacji i bazy danych):** Podpięcie pełnej bazy SQL/PostgreSQL i rozbudowa UI o zakładkę kreatora konsorcjów.
- [ ] **Zadanie 7 (Eksperymenty badawcze):** Przygotowanie min. 20 scenariuszy testowych, policzenie metryk `Precision@5` oraz `Precision@10` i porównanie obu trybów z oceną ekspercką.
