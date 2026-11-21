"""
KROK 1: Pozyskanie danych (Data Acquisition — Wszystkie Dziedziny)
Projekt: Weimar Research Hub
Cel: Zebranie danych znacznie powyżej 300 naukowców (docelowo ~800+) z 9 uczelni
     (po 3 z Polski, Niemiec i Francji) ze WSZYSTKICH głównych dziedzin nauki.
Pobierane atrybuty: afiliacje, dziedzina, publikacje, abstrakty, obszary badań, współautorzy, ORCID.
"""

import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import requests

# Dodanie katalogu głównego do ścieżki Pythona
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import (
    INSTITUTIONS,
    DISCIPLINE_FIELDS,
    AUTHORS_PER_FIELD,
    HTTP_HEADERS,
    RESEARCHERS_FILE,
)

# Thread-local HTTP session dla bezpieczeństwa wielowątkowego
_thread_local = threading.local()

def get_session():
    if not hasattr(_thread_local, "session"):
        s = requests.Session()
        s.headers.update(HTTP_HEADERS)
        _thread_local.session = s
    return _thread_local.session

def fetch_json_with_retry(url, timeout=20, retries=3):
    """Pobiera JSON z prostym mechanizmem ponawiania (obsługa limitu API 429)."""
    session = get_session()
    for attempt in range(retries):
        try:
            resp = session.get(url, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429:
                time.sleep(1.0 * (attempt + 1))
                continue
            return None
        except Exception:
            time.sleep(0.5 * (attempt + 1))
    return None

def reconstruct_abstract(inverted_index):
    """Odtwarza pełny tekst abstraktu ze słownika pozycji OpenAlex (inverted index)."""
    if not inverted_index:
        return ""
    words_by_pos = {}
    for word, positions in inverted_index.items():
        for pos in positions:
            words_by_pos[pos] = word
    return " ".join([words_by_pos[i] for i in sorted(words_by_pos.keys())])

def process_single_author(task_item):
    """Pobiera ostatnie publikacje, abstrakty i współautorów dla pojedynczego naukowca."""
    a, inst, fallback_field = task_item
    raw_id = a.get("id") or ""
    author_id = raw_id.split("/")[-1]
    display_name = a.get("display_name") or "Nieznany Naukowiec"

    orcid = a.get("orcid")
    if not orcid and a.get("ids"):
        orcid = a.get("ids", {}).get("orcid")

    # Główna dziedzina i domena z profilu OpenAlex
    author_topics_raw = a.get("topics") or []
    primary_topic = author_topics_raw[0] if author_topics_raw else {}
    field_name = (primary_topic.get("field") or {}).get("display_name") or fallback_field
    domain_name = (primary_topic.get("domain") or {}).get("display_name") or "Multidisciplinary"
    subfield_name = (primary_topic.get("subfield") or {}).get("display_name") or field_name

    # Pobieranie ostatnich 5 publikacji autora
    works_url = (
        f"https://api.openalex.org/works?"
        f"filter=author.id:{author_id}&per-page=5&sort=publication_year:desc"
    )
    works_json = fetch_json_with_retry(works_url, timeout=15)
    works_data = works_json.get("results", []) if works_json else []

    publications = []
    author_topics = set()
    author_coauthors = set()

    for w in works_data:
        work_id = (w.get("id") or "").split("/")[-1]
        title = w.get("title") or "Brak tytułu"
        pub_year = w.get("publication_year")
        doi = w.get("doi")
        abstract = reconstruct_abstract(w.get("abstract_inverted_index"))

        topics = []
        for t in (w.get("topics") or []):
            t_name = t.get("display_name")
            if t_name:
                topics.append(t_name)
                author_topics.add(t_name)

        for c in (w.get("concepts") or []):
            c_name = c.get("display_name")
            if c_name and c.get("score", 0) > 0.45:
                author_topics.add(c_name)

        for authorship in (w.get("authorships") or []):
            co_author_obj = authorship.get("author") or {}
            other_id = (co_author_obj.get("id") or "").split("/")[-1]
            co_name = co_author_obj.get("display_name")
            if co_name and other_id != author_id:
                author_coauthors.add(co_name)

        publications.append({
            "work_id": work_id,
            "title": title,
            "publication_year": pub_year,
            "doi": doi,
            "abstract": abstract,
            "topics": topics
        })

    for top_topic in author_topics_raw[:8]:
        top_name = top_topic.get("display_name")
        if top_name:
            author_topics.add(top_name)

    stats = a.get("summary_stats") or {}

    return {
        "openalex_id": author_id,
        "name": display_name,
        "orcid": orcid,
        "country": inst["country"],
        "affiliation": inst["short_name"],
        "affiliation_full": inst["name"],
        "city": inst.get("city", ""),
        "openalex_domain": domain_name,
        "field": field_name,
        "subfield": subfield_name,
        "works_count": a.get("works_count", len(publications)),
        "cited_by_count": a.get("cited_by_count", 0),
        "h_index": stats.get("h_index", 0),
        "topics": sorted(list(author_topics)),
        "coauthors": sorted(list(author_coauthors)),
        "publications": publications
    }

def fetch_all_researchers(per_field=AUTHORS_PER_FIELD):
    print("=" * 72, flush=True)
    print("WEIMAR RESEARCH HUB — KROK 1: POZYSKIWANIE DANYCH (WSZYSTKIE DZIEDZINY)", flush=True)
    print(f"Uczelnie: {len(INSTITUTIONS)} | Dziedziny bazowe: {len(DISCIPLINE_FIELDS)}", flush=True)
    print(f"Cel: ~{len(INSTITUTIONS) * len(DISCIPLINE_FIELDS) * per_field} wpisów (po deduplikacji ~700-950 naukowców)", flush=True)
    print("=" * 72, flush=True)

    candidate_tasks = []
    seen_ids = set()

    # Etap 1A: Zebranie listy unikalnych kandydatów z podziałem na dziedziny
    for idx, inst in enumerate(INSTITUTIONS, 1):
        inst_id = inst["id"]
        short = inst["short_name"]
        country = inst["country"]
        inst_candidates = 0

        for field_cfg in DISCIPLINE_FIELDS:
            fid = field_cfg["id"]
            fname = field_cfg["name"]
            url = (
                f"https://api.openalex.org/authors?"
                f"filter=last_known_institutions.id:{inst_id},topics.field.id:{fid}&"
                f"per-page={per_field}&sort=cited_by_count:desc"
            )
            data = fetch_json_with_retry(url)
            if not data:
                continue

            for a in data.get("results", []):
                raw_id = a.get("id") or ""
                author_id = raw_id.split("/")[-1]
                if not author_id or author_id in seen_ids:
                    continue
                seen_ids.add(author_id)
                candidate_tasks.append((a, inst, fname))
                inst_candidates += 1

        print(f"[{idx}/{len(INSTITUTIONS)}] [{country}] {short:<12}: wybrano {inst_candidates} unikalnych naukowców ze wszystkich dziedzin.", flush=True)

    print(f"\nŁącznie wybrano {len(candidate_tasks)} unikalnych naukowców. Pobieranie publikacji i abstraktów...", flush=True)

    # Etap 1B: Równoległe pobieranie publikacji i abstraktów (Polite Pool friendly)
    all_researchers = []
    completed = 0
    total = len(candidate_tasks)

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(process_single_author, task) for task in candidate_tasks]
        for fut in as_completed(futures):
            try:
                rec = fut.result()
                all_researchers.append(rec)
            except Exception as e:
                pass
            completed += 1
            if completed % 100 == 0 or completed == total:
                print(f"  Postęp pobierania prac i abstraktów: {completed}/{total} ({completed/total*100:.0f}%)", flush=True)

    # Stabilne sortowanie po kraju, uczelni i nazwisku
    all_researchers.sort(key=lambda r: (r["country"], r["affiliation"], r["name"]))

    print("\n" + "=" * 72, flush=True)
    print(f"PODSUMOWANIE KROKU 1: Pobrano {len(all_researchers)} unikalnych naukowców!", flush=True)
    print("=" * 72, flush=True)

    # Zapis do plików
    for target_path in [
        RESEARCHERS_FILE,
        CURRENT_DIR / "researchers.json",
        ROOT_DIR / "researchers.json",
    ]:
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(all_researchers, f, ensure_ascii=False, indent=2)

    print(f"Zapisano zbiór danych do: {RESEARCHERS_FILE}", flush=True)
    return all_researchers

if __name__ == "__main__":
    fetch_all_researchers()
