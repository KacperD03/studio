"""
KROK 3: Wyszukiwanie partnerów (Partner Recommendation Engine — Wszystkie Dziedziny)
Projekt: Weimar Research Hub
Cel: Dwa odrębne mechanizmy rekomendacji współpracowników naukowych:
     1. Podobieństwo tematyczne (Topic Similarity) — wyszukiwanie ekspertów w tej samej tematyce
     2. Komplementarność kompetencji (Skill Complementarity) — łączenie uzupełniających się dziedzin
        z zachowaniem merytorycznego punktu styku badawczego.
Technologie: Python, NumPy, Cosine Similarity, pgvector / LSA Embeddings.
"""

import json
import math
import sys
from pathlib import Path
import numpy as np

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import PROFILES_FILE

# Matryca synergii interdyscyplinarnych dla wszystkich dziedzin nauki
INTERDISCIPLINARY_SYNERGY = {
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
    ("Medycyna i Nauki o Zdrowiu", "Nauki Społeczne, Ekonomia i Psychologia"): 0.87,
    ("Medycyna i Nauki o Zdrowiu", "Matematyka i Statystyka"): 0.88,

    ("Biologia, Genetyka i Biotechnologia", "Chemia i Inżynieria Materiałowa"): 0.93,
    ("Biologia, Genetyka i Biotechnologia", "Nauki o Ziemi, Klimacie i Środowisku"): 0.93,
    ("Biologia, Genetyka i Biotechnologia", "Fizyka, Astronomia i Technologie Kwantowe"): 0.86,

    ("Fizyka, Astronomia i Technologie Kwantowe", "Chemia i Inżynieria Materiałowa"): 0.95,
    ("Fizyka, Astronomia i Technologie Kwantowe", "Inżynieria, Energetyka i Robotyka"): 0.94,
    ("Fizyka, Astronomia i Technologie Kwantowe", "Matematyka i Statystyka"): 0.94,

    ("Chemia i Inżynieria Materiałowa", "Inżynieria, Energetyka i Robotyka"): 0.95,
    ("Chemia i Inżynieria Materiałowa", "Nauki o Ziemi, Klimacie i Środowisku"): 0.91,

    ("Inżynieria, Energetyka i Robotyka", "Nauki o Ziemi, Klimacie i Środowisku"): 0.95,
    ("Inżynieria, Energetyka i Robotyka", "Matematyka i Statystyka"): 0.89,
    ("Inżynieria, Energetyka i Robotyka", "Nauki Społeczne, Ekonomia i Psychologia"): 0.85,

    ("Nauki o Ziemi, Klimacie i Środowisku", "Nauki Społeczne, Ekonomia i Psychologia"): 0.93,
    ("Matematyka i Statystyka", "Nauki Społeczne, Ekonomia i Psychologia"): 0.90,
}

def cosine_similarity(v1, v2):
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    a = np.asarray(v1, dtype=np.float64)
    b = np.asarray(v2, dtype=np.float64)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na > 1e-9 and nb > 1e-9:
        return float(np.dot(a, b) / (na * nb))
    return 0.0

def jaccard_similarity(set1, set2):
    s1 = set(x.lower() for x in set1)
    s2 = set(x.lower() for x in set2)
    if not s1 or not s2:
        return 0.0
    return len(s1.intersection(s2)) / len(s1.union(s2))

def get_domain_synergy(domain_a, domain_b, field_a=None, field_b=None):
    """Zwraca wagę synergii interdyscyplinarnej pomiędzy dwiema dziedzinami nauki."""
    if not domain_a or not domain_b:
        return 0.5
    if field_a and field_b and field_a == field_b:
        return 0.20
    if domain_a == domain_b:
        if field_a and field_b and field_a != field_b:
            return 0.60
        return 0.15
    return INTERDISCIPLINARY_SYNERGY.get(
        (domain_a, domain_b),
        INTERDISCIPLINARY_SYNERGY.get((domain_b, domain_a), 0.78)
    )

class PartnerRecommender:
    def __init__(self, data_file=PROFILES_FILE):
        path = Path(data_file)
        if not path.exists():
            path = ROOT_DIR / "krok_2_profilowanie" / "researchers_profiled.json"
        if not path.exists():
            path = ROOT_DIR / "data" / "researchers.json"

        with open(path, "r", encoding="utf-8") as f:
            self.researchers = json.load(f)

        self.by_id = {r["openalex_id"]: r for r in self.researchers}

        # Macierz embeddingów do szybkiego wyliczania Cosine Similarity
        dim = len(self.researchers[0].get("embedding", [])) if self.researchers else 0
        if dim > 0:
            mat = np.array([r.get("embedding", [0.0] * dim) for r in self.researchers], dtype=np.float64)
            norms = np.linalg.norm(mat, axis=1, keepdims=True)
            norms[norms < 1e-9] = 1.0
            self.emb_matrix = mat / norms
            self.id_to_idx = {r["openalex_id"]: i for i, r in enumerate(self.researchers)}
        else:
            self.emb_matrix = None
            self.id_to_idx = {}

    def _get_all_cosines(self, source_id):
        if self.emb_matrix is not None and source_id in self.id_to_idx:
            src_vec = self.emb_matrix[self.id_to_idx[source_id]]
            return self.emb_matrix @ src_vec
        return None

    def recommend_by_similarity(self, source_id, top_k=5, country_filter=None, different_country_only=False):
        """
        Rekomendacja według PODOBIEŃSTWA TEMATYCZNEGO.
        Wyszukuje badaczy o zbliżonej specjalizacji i podobnym profilu publikacji.
        """
        source = self.by_id.get(source_id)
        if not source:
            return []

        cosines = self._get_all_cosines(source_id)
        topics_source = source.get("topics", [])
        comps_source = source.get("competencies", [])
        source_country = source.get("country")
        source_domain = source.get("primary_domain")
        source_field = source.get("field")

        candidates = []
        for idx, r in enumerate(self.researchers):
            cand_id = r["openalex_id"]
            if cand_id == source_id:
                continue
            if country_filter and r.get("country") != country_filter:
                continue
            if different_country_only and r.get("country") == source_country:
                continue

            cos_sim = float(cosines[idx]) if cosines is not None else cosine_similarity(
                source.get("embedding", []), r.get("embedding", [])
            )
            cos_sim = max(0.0, min(1.0, cos_sim))

            topics_cand = r.get("topics", [])
            comps_cand = r.get("competencies", [])

            jac_topics = jaccard_similarity(topics_source, topics_cand)
            jac_comps = jaccard_similarity(comps_source, comps_cand)
            same_field_bonus = 1.0 if r.get("field") == source_field else (0.5 if r.get("primary_domain") == source_domain else 0.0)

            final_score = 0.60 * cos_sim + 0.15 * jac_topics + 0.10 * jac_comps + 0.15 * same_field_bonus
            final_score = max(0.0, min(1.0, final_score))

            shared_topics = sorted(list(set(topics_source).intersection(set(topics_cand))))
            shared_competencies = sorted(list(set(comps_source).intersection(set(comps_cand))))

            candidates.append({
                "researcher": dict(r),
                "score": round(final_score, 4),
                "metric_type": "similarity",
                "similarity_score": round(cos_sim, 4),
                "shared_topics": shared_topics[:5],
                "shared_competencies": shared_competencies[:5],
                "rationale": (
                    f"Wysoka zbieżność tematyczna ({final_score*100:.1f}%). "
                    f"Dyscyplina: {r.get('field')} ({r.get('primary_domain')}). "
                    f"Wspólne obszary: {', '.join(shared_topics[:3]) if shared_topics else 'pokrewne metody badawcze'}."
                )
            })

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_k]

    def recommend_by_complementarity(self, source_id, top_k=5, country_filter=None, different_country_only=False):
        """
        Rekomendacja według KOMPLEMENTARNOŚCI KOMPETENCJI.
        Łączy naukowców z różnych, ale synergicznie uzupełniających się dziedzin
        (np. AI + Medycyna, Fizyka + Materiałoznawstwo, Klimat + Ekonomia)
        przy zachowaniu merytorycznego punktu styku w badaniach.
        """
        source = self.by_id.get(source_id)
        if not source:
            return []

        cosines = self._get_all_cosines(source_id)
        comps_source = set(source.get("competencies", []))
        domain_source = source.get("primary_domain")
        field_source = source.get("field")
        source_country = source.get("country")

        candidates = []
        for idx, r in enumerate(self.researchers):
            cand_id = r["openalex_id"]
            if cand_id == source_id:
                continue
            if country_filter and r.get("country") != country_filter:
                continue
            if different_country_only and r.get("country") == source_country:
                continue

            cos_sim = float(cosines[idx]) if cosines is not None else cosine_similarity(
                source.get("embedding", []), r.get("embedding", [])
            )
            cos_sim = max(0.0, min(1.0, cos_sim))

            domain_cand = r.get("primary_domain")
            field_cand = r.get("field")
            comps_cand = set(r.get("competencies", []))

            synergy = get_domain_synergy(domain_source, domain_cand, field_source, field_cand)

            # Punkt styku (bridge score):
            # W idealnej współpracy interdyscyplinarnej istnieje pewne umiarkowane przecięcie semantyczne
            # (np. cos_sim ~0.15 - 0.55: wspólna metodologia lub obiekt badań), ale bez duplikacji (cos_sim > 0.85)
            bridge_score = math.exp(-((cos_sim - 0.30) ** 2) / (2 * (0.28 ** 2)))

            unique_added = sorted(list(comps_cand - comps_source))
            common_ground = sorted(list(comps_source.intersection(comps_cand)))
            unique_ratio = len(unique_added) / max(1, len(comps_cand))

            # Łączny wynik komplementarności
            comp_score = 0.50 * synergy + 0.32 * bridge_score + 0.18 * unique_ratio
            comp_score = max(0.0, min(1.0, comp_score))

            candidates.append({
                "researcher": dict(r),
                "score": round(comp_score, 4),
                "metric_type": "complementarity",
                "synergy_weight": round(synergy, 3),
                "similarity_baseline": round(cos_sim, 3),
                "partner_unique_skills": unique_added[:5],
                "common_ground": common_ground[:3],
                "rationale": (
                    f"Silna synergia interdyscyplinarna ({comp_score*100:.1f}%): "
                    f"[{field_source}] + [{field_cand}]. "
                    f"Partner wnosi unikalne kompetencje: {', '.join(unique_added[:3]) if unique_added else 'uzupełniające podejście badawcze'}."
                )
            })

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_k]

if __name__ == "__main__":
    recommender = PartnerRecommender()
    if recommender.researchers:
        sample = recommender.researchers[0]
        s_id = sample["openalex_id"]
        print(f"Test dla: {sample['name']} ({sample['affiliation']}, {sample['field']})")
        print("\n--- PODOBIEŃSTWO TEMATYCZNE ---")
        for rec in recommender.recommend_by_similarity(s_id, top_k=3, different_country_only=True):
            print(f"  [{rec['score']*100:.1f}%] {rec['researcher']['name']} ({rec['researcher']['affiliation']}, {rec['researcher']['field']})")
        print("\n--- KOMPLEMENTARNOŚĆ KOMPETENCJI ---")
        for rec in recommender.recommend_by_complementarity(s_id, top_k=3, different_country_only=True):
            print(f"  [{rec['score']*100:.1f}%] {rec['researcher']['name']} ({rec['researcher']['affiliation']}, {rec['researcher']['field']})")
