"""
ETAP 1 (Krok 2 i Krok 3): Profilowanie naukowców i silnik rekomendacji partnerów
Projekt: Weimar Research Hub

Co robi ten plik:
1. Wczytuje sprofilowanych naukowców z pliku `dane_naukowcy.json` (kompetencje,
   dziedziny oraz 128-wymiarowe wektory semantyczne publikacji TF-IDF + SVD).
2. Udostępnia dwa algorytmy wyszukiwania partnerów do współpracy:
   - Tryb 1: PODOBIEŃSTWO TEMATYCZNE (szuka naukowców pracujących nad bardzo podobnym tematem)
   - Tryb 2: KOMPLEMENTARNOŚĆ KOMPETENCJI (łączy naukowców z uzupełniających się dziedzin,
             np. Informatyka/AI + Medycyna lub Fizyka + Inżynieria Materiałowa)

Uruchomienie testu w konsoli (z wewnątrz folderu etap1_prototyp):
    python krok2_profilowanie_i_rekomendacje.py
"""

import json
import math
from pathlib import Path

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

CURRENT_DIR = Path(__file__).resolve().parent
DATA_FILE = CURRENT_DIR / "dane_naukowcy.json"

# Macierz synergii interdyscyplinarnych (określa, jak dobrze uzupełniają się dwie różne dziedziny)
SYNERGIA_DZIEDZIN = {
    ("Informatyka i Sztuczna Inteligencja", "Medycyna i Nauki o Zdrowiu"): 0.96,
    ("Informatyka i Sztuczna Inteligencja", "Biologia, Genetyka i Biotechnologia"): 0.95,
    ("Informatyka i Sztuczna Inteligencja", "Inżynieria, Energetyka i Robotyka"): 0.94,
    ("Informatyka i Sztuczna Inteligencja", "Fizyka, Astronomia i Technologie Kwantowe"): 0.92,
    ("Informatyka i Sztuczna Inteligencja", "Nauki o Ziemi, Klimacie i Środowisku"): 0.91,
    ("Informatyka i Sztuczna Inteligencja", "Nauki Społeczne, Ekonomia i Psychologia"): 0.89,
    ("Informatyka i Sztuczna Inteligencja", "Matematyka i Statystyka"): 0.91,
    ("Informatyka i Sztuczna Inteligencja", "Chemia i Inżynieria Materiałowa"): 0.88,
    ("Medycyna i Nauki o Zdrowiu", "Biologia, Genetyka i Biotechnologia"): 0.96,
    ("Medycyna i Nauki o Zdrowiu", "Chemia i Inżynieria Materiałowa"): 0.92,
    ("Medycyna i Nauki o Zdrowiu", "Inżynieria, Energetyka i Robotyka"): 0.90,
    ("Biologia, Genetyka i Biotechnologia", "Chemia i Inżynieria Materiałowa"): 0.93,
    ("Biologia, Genetyka i Biotechnologia", "Nauki o Ziemi, Klimacie i Środowisku"): 0.93,
    ("Fizyka, Astronomia i Technologie Kwantowe", "Chemia i Inżynieria Materiałowa"): 0.95,
    ("Fizyka, Astronomia i Technologie Kwantowe", "Inżynieria, Energetyka i Robotyka"): 0.94,
    ("Fizyka, Astronomia i Technologie Kwantowe", "Matematyka i Statystyka"): 0.94,
    ("Chemia i Inżynieria Materiałowa", "Inżynieria, Energetyka i Robotyka"): 0.95,
    ("Inżynieria, Energetyka i Robotyka", "Nauki o Ziemi, Klimacie i Środowisku"): 0.95,
    ("Nauki o Ziemi, Klimacie i Środowisku", "Nauki Społeczne, Ekonomia i Psychologia"): 0.93,
}


def podobienstwo_jaccarda(lista1, lista2):
    """Liczy część wspólną dwóch zbiorów słów kluczowych (Indeks Jaccarda: |A i B| / |A lub B|)."""
    s1 = {x.lower() for x in lista1}
    s2 = {x.lower() for x in lista2}
    if not s1 or not s2:
        return 0.0
    return len(s1 & s2) / len(s1 | s2)


def pobierz_synergie_dziedzin(domena_a, domena_b, field_a=None, field_b=None):
    """
    Zwraca współczynnik komplementarności dwóch dziedzin.
    Gdy badacze są z tej samej wąskiej dyscypliny, komplementarność jest niska (0.20),
    natomiast dla uzupełniających się dziedzin (np. AI + Medycyna) wysoka (~0.90-0.96).
    """
    if not domena_a or not domena_b:
        return 0.50
    if field_a and field_b and field_a == field_b:
        return 0.20
    if domena_a == domena_b:
        return 0.55 if (field_a != field_b) else 0.15
    return SYNERGIA_DZIEDZIN.get(
        (domena_a, domena_b),
        SYNERGIA_DZIEDZIN.get((domena_b, domena_a), 0.78)
    )


class SilnikRekomendacji:
    def __init__(self, sciezka_danych=DATA_FILE):
        with open(sciezka_danych, "r", encoding="utf-8") as f:
            self.researchers = json.load(f)

        self.by_id = {r["openalex_id"]: r for r in self.researchers}
        self.id_to_idx = {r["openalex_id"]: i for i, r in enumerate(self.researchers)}

        # Przygotowanie znormalizowanej macierzy wektorów 128-D do szybkiego wyliczania Cosine Similarity
        dim = len(self.researchers[0].get("embedding", [])) if self.researchers else 0
        if HAS_NUMPY and dim > 0:
            mat = np.array([r.get("embedding", [0.0] * dim) for r in self.researchers], dtype=np.float64)
            norms = np.linalg.norm(mat, axis=1, keepdims=True)
            norms[norms < 1e-9] = 1.0
            self.emb_matrix = mat / norms
        else:
            self.emb_matrix = None

    def _policz_cosinusy(self, source_id):
        """Oblicza podobieństwo cosinusowe wektora wybranego naukowca ze wszystkimi w bazie."""
        if self.emb_matrix is not None:
            src_vec = self.emb_matrix[self.id_to_idx[source_id]]
            return self.emb_matrix @ src_vec

        # Fallback w czystym Pythonie (gdyby numpy nie był zainstalowany)
        src_emb = self.by_id[source_id].get("embedding", [])
        return [sum(a * b for a, b in zip(src_emb, r.get("embedding", []))) for r in self.researchers]

    def rekomenduj_podobnych(self, source_id, top_k=5, tylko_zagraniczni=True, kraj=None):
        """
        TRYB 1: Rekomendacja według PODOBIEŃSTWA TEMATYCZNEGO.
        Wzór: 60% Cosine Similarity wektorów 128-D + 25% wspólne tematy/kompetencje + 15% ta sama dziedzina.
        """
        source = self.by_id.get(source_id)
        if not source:
            return []

        cosines = self._policz_cosinusy(source_id)
        wyniki = []

        for idx, kandydat in enumerate(self.researchers):
            if kandydat["openalex_id"] == source_id:
                continue
            if tylko_zagraniczni and kandydat.get("country") == source.get("country"):
                continue
            if kraj and kandydat.get("country") != kraj:
                continue

            cos_sim = max(0.0, min(1.0, float(cosines[idx])))
            jac_tematy = podobienstwo_jaccarda(source.get("topics", []), kandydat.get("topics", []))
            jac_komp = podobienstwo_jaccarda(source.get("competencies", []), kandydat.get("competencies", []))
            bonus_dziedziny = 1.0 if kandydat.get("field") == source.get("field") else (
                0.5 if kandydat.get("primary_domain") == source.get("primary_domain") else 0.0
            )

            score = 0.60 * cos_sim + 0.15 * jac_tematy + 0.10 * jac_komp + 0.15 * bonus_dziedziny
            wspolne_tematy = sorted(set(source.get("topics", [])) & set(kandydat.get("topics", [])))
            wspolne_komp = sorted(set(source.get("competencies", [])) & set(kandydat.get("competencies", [])))

            wyniki.append({
                "researcher": self._bez_wektora(kandydat),
                "score": round(score, 4),
                "cosine_similarity": round(cos_sim, 4),
                "mode": "similarity",
                "shared_topics": wspolne_tematy[:5],
                "shared_competencies": wspolne_komp[:5],
                "explanation_short": (
                    f"Zbieżność wektorów publikacji (Cosine = {cos_sim:.2f}), "
                    f"wspólna dyscyplina: {kandydat.get('field')}. "
                    f"Wspólne słowa kluczowe: {', '.join((wspolne_komp or wspolne_tematy)[:3]) or 'pokrewna metodologia'}."
                )
            })

        wyniki.sort(key=lambda x: x["score"], reverse=True)
        return wyniki[:top_k]

    def rekomenduj_komplementarnych(self, source_id, top_k=5, tylko_zagraniczni=True, kraj=None):
        """
        TRYB 2: Rekomendacja według KOMPLEMENTARNOŚCI KOMPETENCJI.
        Łączy naukowców z uzupełniających się dziedzin, którzy mają umiarkowany punkt styku
        w publikacjach (cos_sim ok. 0.25-0.40), ale wnoszą nowe, unikalne kompetencje.
        """
        source = self.by_id.get(source_id)
        if not source:
            return []

        cosines = self._policz_cosinusy(source_id)
        komp_zrodlo = set(source.get("competencies", []))
        wyniki = []

        for idx, kandydat in enumerate(self.researchers):
            if kandydat["openalex_id"] == source_id:
                continue
            if tylko_zagraniczni and kandydat.get("country") == source.get("country"):
                continue
            if kraj and kandydat.get("country") != kraj:
                continue

            cos_sim = max(0.0, min(1.0, float(cosines[idx])))
            synergia = pobierz_synergie_dziedzin(
                source.get("primary_domain"), kandydat.get("primary_domain"),
                source.get("field"), kandydat.get("field")
            )

            # Punkt styku (bridge_score): najlepszy gdy cos_sim ~ 0.30 (jest wspólny kontekst, ale brak duplikacji)
            bridge_score = math.exp(-((cos_sim - 0.30) ** 2) / (2 * (0.28 ** 2)))

            komp_kandydat = set(kandydat.get("competencies", []))
            nowe_kompetencje = sorted(komp_kandydat - komp_zrodlo)
            wspolne_kompetencje = sorted(komp_zrodlo & komp_kandydat)
            udzial_nowych = len(nowe_kompetencje) / max(1, len(komp_kandydat))

            score = 0.50 * synergia + 0.32 * bridge_score + 0.18 * udzial_nowych

            wyniki.append({
                "researcher": self._bez_wektora(kandydat),
                "score": round(score, 4),
                "cosine_similarity": round(cos_sim, 4),
                "synergy": round(synergia, 2),
                "mode": "complementarity",
                "new_competencies": nowe_kompetencje[:5],
                "shared_competencies": wspolne_kompetencje[:3],
                "explanation_short": (
                    f"Połączenie interdyscyplinarne: [{source.get('field')}] + [{kandydat.get('field')}]. "
                    f"Partner wnosi nowe kompetencje: {', '.join(nowe_kompetencje[:3]) or 'uzupełniający warsztat badawczy'}."
                )
            })

        wyniki.sort(key=lambda x: x["score"], reverse=True)
        return wyniki[:top_k]

    @staticmethod
    def _bez_wektora(rekord):
        kopia = dict(rekord)
        kopia.pop("embedding", None)
        return kopia


if __name__ == "__main__":
    silnik = SilnikRekomendacji()
    agh_naukowiec = next((r for r in silnik.researchers if r.get("affiliation") == "AGH"), silnik.researchers[0])
    sid = agh_naukowiec["openalex_id"]
    emb = agh_naukowiec.get("embedding", [])
    norm_l2 = math.sqrt(sum(x * x for x in emb))

    print("=" * 72)
    print("WEIMAR RESEARCH HUB — TEST PROFILOWANIA I REKOMENDACJI (KROK 2 i 3)")
    print("=" * 72)
    print(f"Wybrany naukowiec: {agh_naukowiec['name']} ({agh_naukowiec['affiliation']}, {agh_naukowiec['country']})")
    print(f"Dziedzina:         {agh_naukowiec['primary_domain']} ({agh_naukowiec['field']})")
    print(f"Kompetencje:       {', '.join(agh_naukowiec.get('competencies', [])[:6])}")
    print(f"Wektor semantyczny: {len(emb)} wymiarów (TF-IDF + SVD), norma L2 = {norm_l2:.4f}")

    print("\n--- TRYB 1: PODOBIEŃSTWO TEMATYCZNE (Partnerzy zagraniczni o tym samym profilu) ---")
    for i, rec in enumerate(silnik.rekomenduj_podobnych(sid, top_k=3, tylko_zagraniczni=True), 1):
        r = rec["researcher"]
        print(f"  {i}. [{rec['score']*100:.1f}%] {r['name']} ({r['affiliation']}, {r['country']}) — {r['field']}")
        print(f"     -> {rec['explanation_short']}")

    print("\n--- TRYB 2: KOMPLEMENTARNOŚĆ KOMPETENCJI (Partnerzy z dziedzin uzupełniających) ---")
    for i, rec in enumerate(silnik.rekomenduj_komplementarnych(sid, top_k=3, tylko_zagraniczni=True), 1):
        r = rec["researcher"]
        print(f"  {i}. [{rec['score']*100:.1f}%] {r['name']} ({r['affiliation']}, {r['country']}) — {r['field']}")
        print(f"     -> {rec['explanation_short']}")
    print("=" * 72)
