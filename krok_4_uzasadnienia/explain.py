"""
KROK 4: Uzasadnianie rekomendacji (Recommendation Explainability & RAG)
Projekt: Weimar Research Hub (Wszystkie Dziedziny)
Cel: Dla każdego proponowanego partnera wskazywać, dlaczego współpraca jest wartościowa,
     z bezpośrednim odwołaniem do KONKRETNYCH publikacji i abstraktów obu naukowców.
Technologie: LLM (opcjonalny OpenAI API) + RAG (Retrieval-Augmented Generation), PostgreSQL / SQLite.
"""

import json
import os
import re
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import PROFILES_FILE

RAG_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "are", "was", "were",
    "have", "has", "been", "being", "their", "which", "such", "also", "more",
    "most", "can", "may", "will", "into", "over", "under", "between", "among",
    "through", "using", "used", "based", "study", "studies", "paper", "results",
    "result", "method", "methods", "approach", "approaches", "model", "models",
    "analysis", "system", "systems", "data", "high", "low", "new", "novel",
    "large", "small", "different", "various", "important", "significant", "show",
    "shown", "present", "presented", "proposed", "propose", "however", "while",
    "both", "two", "three", "one", "well", "these", "those", "than", "then",
    "when", "where", "who", "whom", "what", "how", "all", "each", "other",
    "only", "some", "many", "several", "first", "second", "work", "research",
    "science", "scientific", "article", "review", "state", "effect", "effects",
    "performance", "properties", "application", "applications", "during", "about",
    "after", "before", "under", "within", "without", "across", "potential",
    "abstract", "introduction", "background", "conclusion", "conclusions",
    "purpose", "objective", "objectives", "summary", "advanced", "conditions",
    "focus", "level", "aspects", "important", "role", "current", "recent"
}

def extract_meaningful_terms(pub):
    """Wyciąga wartościowe terminy naukowe z tytułu, abstraktu i tematów publikacji."""
    text = " ".join([
        pub.get("title") or "",
        pub.get("abstract") or "",
        " ".join(pub.get("topics") or [])
    ]).lower()
    words = re.findall(r"\b[a-z]{4,}\b", text)
    return {w for w in words if w not in RAG_STOPWORDS}

def find_best_matching_publications(pubs_a, pubs_b):
    """
    Krok Retrieval (RAG): Dopasowuje parę konkretnych publikacji (p_A, p_B)
    o największym wspólnym mianowniku naukowym.
    """
    valid_a = [p for p in pubs_a if p.get("title") and p.get("title") != "Brak tytułu"]
    valid_b = [p for p in pubs_b if p.get("title") and p.get("title") != "Brak tytułu"]

    if not valid_a:
        valid_a = [{"title": "Ostatnie prace badawcze", "publication_year": 2024, "abstract": "", "topics": []}]
    if not valid_b:
        valid_b = [{"title": "Ostatnie prace badawcze", "publication_year": 2024, "abstract": "", "topics": []}]

    best_pair = None
    max_score = -1

    for pa in valid_a:
        terms_a = extract_meaningful_terms(pa)
        topics_a = {t.lower() for t in (pa.get("topics") or [])}
        for pb in valid_b:
            terms_b = extract_meaningful_terms(pb)
            topics_b = {t.lower() for t in (pb.get("topics") or [])}

            common_words = sorted(list(terms_a.intersection(terms_b)))
            common_topics = topics_a.intersection(topics_b)

            # Premia za wspólne słowa kluczowe, abstrakt i tematy
            score = len(common_words) + 3 * len(common_topics)
            if pa.get("abstract") and pb.get("abstract"):
                score += 1

            if score > max_score:
                max_score = score
                best_pair = {
                    "pub_a": pa,
                    "pub_b": pb,
                    "overlap_keywords": common_words[:6],
                    "common_topics": list(common_topics)[:3]
                }

    return best_pair

class RecommendationExplainer:
    def __init__(self, data_file=PROFILES_FILE):
        path = Path(data_file)
        if not path.exists():
            path = ROOT_DIR / "krok_2_profilowanie" / "researchers_profiled.json"
        if not path.exists():
            path = ROOT_DIR / "data" / "researchers.json"

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.by_id = {r["openalex_id"]: r for r in data}

    def _try_llm_explain(self, prompt):
        """Opcjonalne wywołanie OpenAI API, jeśli ustawiono OPENAI_API_KEY."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None
        try:
            import requests
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.4,
                    "max_tokens": 350
                },
                timeout=12
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            pass
        return None

    def explain_recommendation(self, source_id, target_id, rec_type="complementarity"):
        """Generuje merytoryczne uzasadnienie RAG z cytowaniem konkretnych prac."""
        source = self.by_id.get(source_id)
        target = self.by_id.get(target_id)

        if not source or not target:
            return {"error": "Nie znaleziono jednego z naukowców."}

        name_a = source.get("name")
        affil_a = f"{source.get('affiliation')} ({source.get('country')})"
        field_a = source.get("field") or source.get("primary_domain", "Nauka")
        domain_a = source.get("primary_domain", field_a)

        name_b = target.get("name")
        affil_b = f"{target.get('affiliation')} ({target.get('country')})"
        field_b = target.get("field") or target.get("primary_domain", "Nauka")
        domain_b = target.get("primary_domain", field_b)

        # Retrieval (RAG)
        evidence = find_best_matching_publications(
            source.get("publications", []),
            target.get("publications", [])
        )
        pub_a = evidence["pub_a"]
        pub_b = evidence["pub_b"]
        keywords = evidence["overlap_keywords"]

        title_a = pub_a.get("title", "Publikacja bazowa")
        year_a = pub_a.get("publication_year") or "b.d."
        raw_abs_a = re.sub(r"^abstract[\s:.\-]+", "", (pub_a.get("abstract") or "").strip(), flags=re.IGNORECASE)
        abs_a_snippet = raw_abs_a[:140].strip()

        title_b = pub_b.get("title", "Publikacja partnerska")
        year_b = pub_b.get("publication_year") or "b.d."
        raw_abs_b = re.sub(r"^abstract[\s:.\-]+", "", (pub_b.get("abstract") or "").strip(), flags=re.IGNORECASE)
        abs_b_snippet = raw_abs_b[:140].strip()

        kw_str = ", ".join(keywords[:4]) if keywords else "zbieżna metodologia badawcza"

        # Próba użycia zewnętrznego LLM jeśli dostępny klucz API
        llm_prompt = (
            f"Uzasadnij krótko po polsku dlaczego współpraca naukowa między {name_a} ({affil_a}, {field_a}) "
            f"a {name_b} ({affil_b}, {field_b}) w trybie '{rec_type}' jest wartościowa. "
            f"Odwołaj się wprost do pracy A: '{title_a}' ({year_a}) oraz pracy B: '{title_b}' ({year_b}). "
            f"Wspólne pojęcia: {kw_str}."
        )
        llm_text = self._try_llm_explain(llm_prompt)

        if llm_text:
            rationale_text = llm_text
            mode_title = "Podobieństwo tematyczne (RAG + LLM)" if rec_type == "similarity" else "Komplementarność kompetencji (RAG + LLM)"
        elif rec_type == "similarity":
            mode_title = "Wspólny front badawczy (Podobieństwo tematyczne)"
            rationale_text = (
                f"Współpraca pomiędzy {name_a} ({affil_a}) a {name_b} ({affil_b}) bazuje na silnej "
                f"zbieżności naukowej w dyscyplinie {field_a} (obszar: {domain_a}).\n\n"
                f"Dowody z dorobku publikacyjnego:\n"
                f"• {name_a} w pracy „{title_a}” ({year_a}) bada zagadnienia z zakresu: {kw_str}.\n"
                f"• {name_b} w pracy „{title_b}” ({year_b}) rozwija bardzo zbliżoną tematykę i narzędzia.\n\n"
                f"Wartość dodana: Wspólne kompetencje ułatwiają bezpośrednie przygotowanie wspólnych artykułów "
                f"w czasopismach międzynarodowych oraz wymianę danych i benchmarków."
            )
        else:
            mode_title = "Synergia interdyscyplinarna (Komplementarność kompetencji)"
            rationale_text = (
                f"Połączenie {name_a} ({affil_a}, {field_a}) oraz {name_b} ({affil_b}, {field_b}) "
                f"tworzy silne interdyscyplinarne konsorcjum łączące obszar [{domain_a}] z [{domain_b}].\n\n"
                f"Dowody z dorobku publikacyjnego:\n"
                f"• {name_a} w publikacji „{title_a}” ({year_a}) dostarcza metodologii ze swojej dziedziny"
                f"{f' („{abs_a_snippet}...”).' if abs_a_snippet else '.'}\n"
                f"• {name_b} w publikacji „{title_b}” ({year_b}) wnosi brakującą perspektywę uzupełniającą"
                f"{f' („{abs_b_snippet}...”).' if abs_b_snippet else '.'}\n"
                f"• Punkt styku badawczego: {kw_str}.\n\n"
                f"Wartość dodana: Takie zestawienie kompetencji zwiększa szanse w europejskich konkursach grantowych "
                f"(Horizon Europe, programy NCN–DFG–ANR Trójkąta Weimarskiego)."
            )

        return {
            "mode": mode_title,
            "researcher_a": {
                "id": source_id,
                "name": name_a,
                "affiliation": affil_a,
                "field": field_a,
                "domain": domain_a,
                "cited_publication": {
                    "title": title_a,
                    "year": year_a,
                    "doi": pub_a.get("doi")
                }
            },
            "researcher_b": {
                "id": target_id,
                "name": name_b,
                "affiliation": affil_b,
                "field": field_b,
                "domain": domain_b,
                "cited_publication": {
                    "title": title_b,
                    "year": year_b,
                    "doi": pub_b.get("doi")
                }
            },
            "shared_keywords": keywords,
            "detailed_explanation": rationale_text
        }

if __name__ == "__main__":
    explainer = RecommendationExplainer()
    keys = list(explainer.by_id.keys())
    if len(keys) >= 2:
        res = explainer.explain_recommendation(keys[0], keys[1], rec_type="complementarity")
        print(res["detailed_explanation"])
