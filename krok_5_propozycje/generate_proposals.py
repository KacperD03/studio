"""
KROK 5: Generowanie propozycji współpracy (Collaboration Proposal Generator — Wszystkie Dziedziny)
Projekt: Weimar Research Hub
Cel: Dla wybranych 2-3 naukowców automatycznie proponować spójny temat wspólnych badań,
     podział kompetencji (pakiety robocze) oraz potencjalne rezultaty.
Technologie: LLM (OpenAI API / lokalny generator semantyczny), Python.
"""

import json
import os
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import PROFILES_FILE

# Krótkie kody domen do budowania zgrabnych akronimów i spójnych tematów projektów
DOMAIN_META = {
    "Informatyka i Sztuczna Inteligencja": ("AI", "algorytmów sztucznej inteligencji i analizy danych"),
    "Medycyna i Nauki o Zdrowiu": ("MED", "diagnostyki klinicznej i medycyny translacyjnej"),
    "Biologia, Genetyka i Biotechnologia": ("BIO", "biologii molekularnej i biotechnologii"),
    "Fizyka, Astronomia i Technologie Kwantowe": ("PHYS", "zaawansowanej fizyki i technologii kwantowych"),
    "Chemia i Inżynieria Materiałowa": ("MAT", "nowych materiałów funkcjonalnych i inżynierii chemicznej"),
    "Inżynieria, Energetyka i Robotyka": ("ENG", "nowoczesnej inżynierii systemów i czystej energii"),
    "Matematyka i Statystyka": ("MATH", "modelowania matematycznego i analizy stochastycznej"),
    "Nauki o Ziemi, Klimacie i Środowisku": ("ECO", "zrównoważonego środowiska i monitoringu klimatu"),
    "Nauki Społeczne, Ekonomia i Psychologia": ("SOC", "analiz społeczno-ekonomicznych i polityk innowacji"),
}

def shorten_skill(skill):
    """Skraca zbyt długie etykiety tematyczne z OpenAlex do zgrabnej frazy."""
    if not skill:
        return "badania specjalistyczne"
    words = skill.split()
    return " ".join(words[:4]) if len(words) > 4 else skill

class ProposalGenerator:
    def __init__(self, data_file=PROFILES_FILE):
        path = Path(data_file)
        if not path.exists():
            path = ROOT_DIR / "krok_2_profilowanie" / "researchers_profiled.json"
        if not path.exists():
            path = ROOT_DIR / "data" / "researchers.json"

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.by_id = {r["openalex_id"]: r for r in data}

    def _try_llm_proposal(self, selected):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None
        try:
            import requests
            desc = "\n".join([
                f"- {r['name']} ({r['affiliation']}, {r['country']}): dyscyplina {r.get('field')}, kompetencje: {', '.join(r.get('competencies', [])[:4])}"
                for r in selected
            ])
            prompt = (
                f"Zaproponuj po polsku wspólny projekt badawczy dla konsorcjum naukowców:\n{desc}\n"
                f"Zwróć wyłącznie poprawny JSON z kluczami: project_title (string), acronym (string), scientific_rationale (string)."
            )
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.5,
                    "max_tokens": 400
                },
                timeout=15
            )
            if resp.status_code == 200:
                return json.loads(resp.json()["choices"][0]["message"]["content"])
        except Exception:
            pass
        return None

    def generate_proposal(self, researcher_ids):
        """Generuje spójną propozycję projektu badawczego dla 2 lub 3 wybranych naukowców."""
        if not (2 <= len(researcher_ids) <= 3):
            return {"error": "Należy wybrać dokładnie 2 lub 3 naukowców."}

        selected = [self.by_id.get(rid) for rid in researcher_ids if self.by_id.get(rid)]
        if len(selected) != len(researcher_ids):
            return {"error": "Nie odnaleziono niektórych naukowców w bazie."}

        names = [r.get("name") for r in selected]
        affils = [f"{r.get('affiliation')} ({r.get('country')})" for r in selected]
        domains = [r.get("primary_domain", "Nauki Ścisłe") for r in selected]
        fields = [r.get("field", "Research") for r in selected]

        # Kody i opisy dla budowania eleganckiego tytułu i akronimu
        codes = []
        phrases = []
        for dom in domains:
            code, phrase = DOMAIN_META.get(dom, ("SCI", "badań interdyscyplinarnych"))
            if code not in codes:
                codes.append(code)
            if phrase not in phrases:
                phrases.append(phrase)

        focus_skills = [
            shorten_skill((r.get("competencies") or [r.get("field", "Research")])[0])
            for r in selected
        ]

        llm_override = self._try_llm_proposal(selected)

        if llm_override and llm_override.get("project_title"):
            project_title = llm_override["project_title"]
            acronym = llm_override.get("acronym", f"WEIMAR-{'-'.join(codes[:3])}")
            rationale = llm_override.get("scientific_rationale", "")
        else:
            acronym = f"WEIMAR-{'-'.join(codes[:3])}"
            if len(phrases) == 1:
                project_title = (
                    f"Europejska platforma badawcza w zakresie {phrases[0]}: "
                    f"synergia metod {focus_skills[0]} oraz {focus_skills[1]}"
                )
            elif len(phrases) == 2:
                project_title = (
                    f"Interdyscyplinarna integracja {phrases[0]} z obszarami {phrases[1]} "
                    f"w oparciu o {focus_skills[0]}"
                )
            else:
                project_title = (
                    f"Trójstronny program badawczy na styku {phrases[0]}, {phrases[1]} "
                    f"oraz {phrases[2]}"
                )

            unique_fields = ", ".join(dict.fromkeys(fields))
            rationale = (
                f"Projekt łączy komplementarne ośrodki z {', '.join(affils)} w celu rozwiązania złożonych "
                f"wyzwań badawczych wymagających współpracy dyscyplin: {unique_fields}. "
                f"Zestawienie zaplecza metodycznego ({'; '.join(focus_skills)}) umożliwia przejście od badań "
                f"cząstkowych do kompleksowej walidacji teoretycznej i eksperymentalnej na poziomie europejskim."
            )

        work_packages = []
        competency_division = {}

        for idx, r in enumerate(selected, 1):
            r_name = r.get("name")
            r_affil = r.get("affiliation")
            r_field = r.get("field", r.get("primary_domain"))
            r_domain = r.get("primary_domain")
            r_skills = [shorten_skill(s) for s in (r.get("competencies") or [])[:4]]
            r_pubs = [p.get("title") for p in r.get("publications", []) if p.get("title") and p.get("title") != "Brak tytułu"][:1]
            pub_ref = f"„{r_pubs[0]}”" if r_pubs else "dotychczasowy dorobek zespołu"

            role_desc = {
                "lider_obszaru": f"Kierownik Pakietu Roboczego WP{idx}",
                "afiliacja": f"{r_affil} ({r.get('country')})",
                "domena": f"{r_field} ({r_domain})",
                "wnoszone_kompetencje": r_skills,
                "kluczowe_zadania": [
                    f"Opracowanie komponentu badawczego w zakresie: {', '.join(r_skills[:2]) if r_skills else r_field}.",
                    f"Wykorzystanie i rozwój metodologii z pracy: {pub_ref}.",
                    f"Wymiana naukowa doktorantów i walidacja wyników w laboratorium {r_affil}."
                ]
            }
            competency_division[r_name] = role_desc

            work_packages.append({
                "wp_id": f"WP{idx}",
                "nazwa": f"Komponent specjalistyczny: {r_field}",
                "lider": f"{r_name} ({r_affil})",
                "zadania": role_desc["kluczowe_zadania"]
            })

        work_packages.append({
            "wp_id": f"WP{len(selected) + 1}",
            "nazwa": "Integracja interdyscyplinarna, wspólna walidacja i przygotowanie wniosku grantowego",
            "lider": "Całe konsorcjum (PL–DE–FR)",
            "zadania": [
                "Połączenie wyników prac teoretycznych, eksperymentalnych i obliczeniowych w spójny model.",
                "Wspólna walidacja na rzeczywistych zbiorach danych lub próbkach laboratoryjnych.",
                "Przygotowanie wspólnych publikacji oraz aplikacji do programów Horizon Europe / NCN–DFG–ANR."
            ]
        })

        expected_outcomes = {
            "publikacje": [
                f"3–4 wspólne artykuły w renomowanych czasopismach Q1 łączących dyscypliny {', '.join(dict.fromkeys(fields[:3]))}",
                "Prezentacja wyników na wiodących międzynarodowych kongresach naukowych"
            ],
            "oprogramowanie_i_artefakty": [
                "Wspólne repozytorium narzędzi, modeli obliczeniowych lub otwartych protokołów badawczych (Open Science)",
                "Zunifikowany zbiór danych benchmarkowych i dokumentacja metodologiczna"
            ],
            "aplikacje_grantowe": [
                "Wniosek do programu Horizon Europe (ERC Synergy / Cluster Research & Innovation)",
                "Trójstronny projekt polsko-niemiecko-francuski (NCN – DFG – ANR w ramach Trójkąta Weimarskiego)"
            ],
            "wymiar_miedzynarodowy": (
                "Trwałe partnerstwo pomiędzy ośrodkami w Polsce, Niemczech i Francji, w tym wspólne "
                "promotorstwa doktoratów (co-tutelle) i wymiana kadry badawczej."
            )
        }

        proposal = {
            "project_title": project_title,
            "acronym": acronym,
            "consortium": [
                {
                    "name": r.get("name"),
                    "affiliation": r.get("affiliation"),
                    "country": r.get("country"),
                    "field": r.get("field"),
                    "domain": r.get("primary_domain")
                }
                for r in selected
            ],
            "scientific_rationale": rationale,
            "competency_division": competency_division,
            "work_packages": work_packages,
            "expected_outcomes": expected_outcomes
        }

        try:
            from database.db import get_connection
            conn, _ = get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO collaboration_proposals
                (researcher_ids, researcher_names, project_title, scientific_rationale,
                 competency_division, expected_outcomes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                json.dumps(researcher_ids),
                json.dumps(names, ensure_ascii=False),
                project_title,
                rationale,
                json.dumps(competency_division, ensure_ascii=False),
                json.dumps(expected_outcomes, ensure_ascii=False)
            ))
            conn.commit()
            conn.close()
        except Exception:
            pass

        return proposal

if __name__ == "__main__":
    gen = ProposalGenerator()
    keys = list(gen.by_id.keys())
    if len(keys) >= 3:
        prop = gen.generate_proposal([keys[0], keys[1], keys[2]])
        print(f"TYTUŁ: {prop['project_title']}\nAKRONIM: {prop['acronym']}")
