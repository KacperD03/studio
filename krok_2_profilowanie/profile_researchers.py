"""
KROK 2: Profilowanie naukowców (Researcher Profiling — Wszystkie Dziedziny)
Projekt: Weimar Research Hub
Cel: Automatyczne wyznaczanie kompetencji, dyscyplin naukowych, biogramu badawczego
     oraz gęstych wektorów semantycznych (embeddings) na podstawie publikacji i abstraktów.
Technologie: Python, Sentence Transformers / TF-IDF + SVD (LSA Embeddings), LLM-style synthesis.
"""

import json
import math
import os
import re
import sys
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds

# Dodanie katalogu głównego do ścieżki
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import RESEARCHERS_FILE, PROFILES_FILE

# Taksonomia wielodziedzinowa (wszystkie główne obszary nauki)
SCIENTIFIC_DOMAINS = {
    "Informatyka i Sztuczna Inteligencja": [
        "machine learning", "deep learning", "neural network", "artificial intelligence",
        "computer vision", "natural language processing", "reinforcement learning",
        "transformer", "large language model", "cybersecurity", "cryptography",
        "distributed systems", "cloud computing", "software engineering", "algorithm",
        "data mining", "knowledge graph", "blockchain", "computer science"
    ],
    "Medycyna i Nauki o Zdrowiu": [
        "clinical", "oncology", "cancer", "tumor", "cardiology", "therapy",
        "patient", "diagnosis", "immunology", "epidemiology", "neurology",
        "surgery", "pathology", "radiology", "medical imaging", "biomarker",
        "vaccine", "cardiovascular", "clinical trial", "medicine", "healthcare"
    ],
    "Biologia, Genetyka i Biotechnologia": [
        "genomics", "genetics", "dna", "rna", "protein", "molecular biology",
        "cell biology", "bioinformatics", "microbiology", "crispr", "gene expression",
        "enzyme", "metabolomics", "neuroscience", "biotechnology", "evolution",
        "sequencing", "biochemistry", "transcriptomics"
    ],
    "Fizyka, Astronomia i Technologie Kwantowe": [
        "quantum", "photonics", "laser", "particle physics", "astrophysics",
        "cosmology", "condensed matter", "optics", "plasma", "superconductivity",
        "spectroscopy", "magnetic", "detector", "relativity", "semiconductor",
        "quantum computing", "quantum mechanics", "physics"
    ],
    "Chemia i Inżynieria Materiałowa": [
        "catalysis", "polymer", "nanomaterials", "nanoparticles", "synthesis",
        "electrochemistry", "graphene", "crystal", "alloy", "materials science",
        "organic chemistry", "inorganic chemistry", "molecular dynamics",
        "composite", "membrane", "photocatalysis", "battery", "corrosion"
    ],
    "Inżynieria, Energetyka i Robotyka": [
        "robotics", "control systems", "autonomous", "sensor", "energy",
        "renewable energy", "solar", "photovoltaic", "signal processing",
        "manufacturing", "thermodynamics", "aerospace", "mechanical",
        "electrical engineering", "smart grid", "automation", "mechatronics"
    ],
    "Matematyka i Statystyka": [
        "differential equation", "topology", "algebra", "stochastic", "probability",
        "optimization", "numerical analysis", "geometry", "bayesian", "combinatorics",
        "graph theory", "computational mathematics", "functional analysis",
        "partial differential", "statistics", "mathematical modeling"
    ],
    "Nauki o Ziemi, Klimacie i Środowisku": [
        "climate change", "ecology", "hydrology", "geology", "sustainability",
        "biodiversity", "atmosphere", "carbon", "ecosystem", "water quality",
        "remote sensing", "geophysics", "soil", "air pollution", "marine",
        "environmental science", "glacier", "decarbonization"
    ],
    "Nauki Społeczne, Ekonomia i Psychologia": [
        "economics", "econometrics", "finance", "sociology", "governance",
        "public policy", "psychology", "cognition", "education", "behavior",
        "innovation policy", "labor market", "macroeconomics", "sustainability policy",
        "social network", "ethics", "political science", "demography"
    ]
}

# Mapowanie nazw dyscyplin z OpenAlex -> polskie kategorie dziedzinowe
OPENALEX_FIELD_MAP = {
    "Computer Science": "Informatyka i Sztuczna Inteligencja",
    "Decision Sciences": "Informatyka i Sztuczna Inteligencja",
    "Medicine": "Medycyna i Nauki o Zdrowiu",
    "Nursing": "Medycyna i Nauki o Zdrowiu",
    "Health Professions": "Medycyna i Nauki o Zdrowiu",
    "Dentistry": "Medycyna i Nauki o Zdrowiu",
    "Pharmacology, Toxicology and Pharmaceutics": "Medycyna i Nauki o Zdrowiu",
    "Biochemistry, Genetics and Molecular Biology": "Biologia, Genetyka i Biotechnologia",
    "Immunology and Microbiology": "Biologia, Genetyka i Biotechnologia",
    "Neuroscience": "Biologia, Genetyka i Biotechnologia",
    "Agricultural and Biological Sciences": "Biologia, Genetyka i Biotechnologia",
    "Physics and Astronomy": "Fizyka, Astronomia i Technologie Kwantowe",
    "Chemistry": "Chemia i Inżynieria Materiałowa",
    "Chemical Engineering": "Chemia i Inżynieria Materiałowa",
    "Materials Science": "Chemia i Inżynieria Materiałowa",
    "Engineering": "Inżynieria, Energetyka i Robotyka",
    "Energy": "Inżynieria, Energetyka i Robotyka",
    "Mathematics": "Matematyka i Statystyka",
    "Environmental Science": "Nauki o Ziemi, Klimacie i Środowisku",
    "Earth and Planetary Sciences": "Nauki o Ziemi, Klimacie i Środowisku",
    "Social Sciences": "Nauki Społeczne, Ekonomia i Psychologia",
    "Economics, Econometrics and Finance": "Nauki Społeczne, Ekonomia i Psychologia",
    "Business, Management and Accounting": "Nauki Społeczne, Ekonomia i Psychologia",
    "Psychology": "Nauki Społeczne, Ekonomia i Psychologia",
    "Arts and Humanities": "Nauki Społeczne, Ekonomia i Psychologia"
}

STOPWORDS = {
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
    "science", "scientific", "article", "review", "journal", "university",
    "abstract", "introduction", "background", "conclusion", "conclusions",
    "purpose", "objective", "objectives", "summary", "advanced", "focus", "level"
}

GENERIC_TOPICS = {
    "computer science", "medicine", "physics", "chemistry", "engineering",
    "mathematics", "biology", "social sciences", "economics", "science",
    "research", "technology", "materials science", "environmental science",
    "artificial intelligence", "quantum mechanics", "genetics"
}

def clean_text(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9\s-]", " ", text)
    return " ".join(text.split())

def tokenize(text):
    """Tokenizacja z filtrowaniem stopwords do TF-IDF/LSA."""
    cleaned = clean_text(text)
    tokens = [w for w in cleaned.split() if len(w) >= 3 and w not in STOPWORDS and not w.isdigit()]
    # Dodajemy bigramy dla wyższej precyzji semantycznej
    bigrams = [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens) - 1)]
    return tokens + bigrams

def extract_competencies(researcher):
    """
    Wyznacza główną i poboczną domenę naukową oraz listę konkretnych kompetencji
    na podstawie abstraktów, tytułów publikacji, tematów i metadanych OpenAlex.
    """
    oa_field = researcher.get("field", "")
    oa_subfield = researcher.get("subfield", "")

    pub_texts = " ".join([
        researcher.get("subfield", ""),
        " ".join(researcher.get("topics", [])),
        " ".join([p.get("title", "") for p in researcher.get("publications", [])]),
        " ".join([p.get("abstract", "") for p in researcher.get("publications", [])])
    ])
    cleaned = clean_text(pub_texts)

    domain_scores = Counter()
    skill_counts = Counter()

    # Punktacja na bazie słów kluczowych z publikacji i abstraktów
    for domain, keywords in SCIENTIFIC_DOMAINS.items():
        for kw in keywords:
            matches = len(re.findall(r"\b" + re.escape(kw) + r"\b", cleaned))
            if matches > 0:
                domain_scores[domain] += matches
                skill_counts[kw.title()] += matches

    # Silny priorytet dla oficjalnej dyscypliny z OpenAlex
    mapped_oa = OPENALEX_FIELD_MAP.get(oa_field)
    if mapped_oa:
        domain_scores[mapped_oa] += 8

    top_domains = [d for d, _ in domain_scores.most_common(2)]
    if not top_domains:
        top_domains = [mapped_oa or "Nauki Ścisłe i Inżynieryjne"]

    # Sortowanie kompetencji wg częstości wystąpień (eliminuje przypadkowe pojedyncze wzmianki)
    matched_skills = [s for s, cnt in skill_counts.most_common() if cnt >= 2]
    if not matched_skills:
        matched_skills = [s for s, _ in skill_counts.most_common(4)]

    # Dobór szczegółowych kompetencji z OpenAlex topics i słów kluczowych
    candidate_topics = []
    if oa_subfield and oa_subfield.lower() not in GENERIC_TOPICS:
        candidate_topics.append(oa_subfield)

    for t in researcher.get("topics", []):
        t_clean = t.strip()
        if len(t_clean) > 3 and t_clean.lower() not in GENERIC_TOPICS:
            if t_clean not in candidate_topics:
                candidate_topics.append(t_clean)

    # Połączenie konkretnych kompetencji (unikalnych i zwięzłych)
    combined_skills = []
    for item in matched_skills + candidate_topics:
        if item not in combined_skills and len(item) <= 55:
            combined_skills.append(item)
        if len(combined_skills) >= 8:
            break

    if not combined_skills:
        combined_skills = [oa_subfield or oa_field or "Interdisciplinary Research"]

    return {
        "primary_domain": top_domains[0],
        "secondary_domain": top_domains[1] if len(top_domains) > 1 else None,
        "competencies": combined_skills,
        "domain_scores": dict(domain_scores)
    }

def generate_profile_summary(researcher, comp_info):
    """Generuje zwięzły, merytoryczny biogram badawczy po polsku."""
    name = researcher.get("name", "Naukowiec")
    affil = researcher.get("affiliation", "Uczelnia")
    country_name = {"PL": "Polsce", "DE": "Niemczech", "FR": "Francji"}.get(researcher.get("country"), "Europie")
    primary_domain = comp_info["primary_domain"]
    oa_field = researcher.get("field", primary_domain)
    competencies_str = ", ".join(comp_info["competencies"][:5])

    pubs = researcher.get("publications", [])
    recent_titles = [p.get("title") for p in pubs if p.get("title") and p.get("title") != "Brak tytułu"][:2]

    works_cnt = researcher.get("works_count", len(pubs))
    cited_cnt = researcher.get("cited_by_count", 0)
    h_idx = researcher.get("h_index", 0)

    lines = [
        f"{name} ({affil}, {country_name}) prowadzi badania w obszarze: {primary_domain} (dyscyplina: {oa_field}).",
        f"Kluczowe kompetencje badawcze: {competencies_str}.",
        f"Dorobek: {works_cnt} publikacji, {cited_cnt} cytowań (h-index: {h_idx})."
    ]
    if recent_titles:
        formatted = " oraz ".join([f"„{t}”" for t in recent_titles])
        lines.append(f"Ostatnie publikacje: {formatted}.")
    return " ".join(lines)

def build_semantic_embeddings(researchers_list, comp_infos, target_dim=128):
    """
    Buduje gęste, znormalizowane L2 wektory semantyczne (Embeddings).
    Najpierw próbuje użyć SentenceTransformers (jeśli dostępne na danej maszynie),
    a w przeciwnym razie wylicza wektory metodą TF-IDF + Truncated SVD (LSA)
    na pełnym korpusie publikacji i abstraktów całego zbioru naukowców.
    """
    corpus_texts = []
    for r, comp in zip(researchers_list, comp_infos):
        # Bogaty dokument reprezentujący profil naukowy badacza
        doc = " ".join([
            r.get("field", ""),
            r.get("subfield", ""),
            comp["primary_domain"],
            " ".join(comp["competencies"]),
            " ".join(r.get("topics", [])),
            " ".join([p.get("title", "") for p in r.get("publications", [])]),
            " ".join([p.get("abstract", "") for p in r.get("publications", [])])
        ])
        corpus_texts.append(doc)

    # Próba użycia Sentence Transformers (aktywowana zmienną USE_SENTENCE_TRANSFORMERS=1)
    if os.environ.get("USE_SENTENCE_TRANSFORMERS") == "1":
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")
            embs = model.encode(corpus_texts, normalize_embeddings=True, show_progress_bar=False)
            print("[EMBEDDINGS] Użyto modelu neuronowego SentenceTransformers (all-MiniLM-L6-v2).")
            return [[round(float(x), 5) for x in row] for row in embs]
        except Exception as e:
            print(f"[EMBEDDINGS] Uwaga: SentenceTransformers niedostępne ({e}), przejście na TF-IDF + SVD.")

    # Fallback wysokiej jakości: TF-IDF + SVD (Latent Semantic Analysis) w SciPy/NumPy
    print("[EMBEDDINGS] Budowanie przestrzeni semantycznej TF-IDF + SVD (LSA 128-D)...")
    tokenized_docs = [tokenize(doc) for doc in corpus_texts]

    # Zliczanie częstości dokumentowej (Document Frequency)
    df = Counter()
    for tokens in tokenized_docs:
        df.update(set(tokens))

    n_docs = len(tokenized_docs)
    # Wybór słownika terminów pojawiających się w min. 2 dokumentach i max 65% dokumentów
    vocab = [
        term for term, count in df.items()
        if count >= 2 and count <= int(0.65 * n_docs)
    ]
    # Limit słownika do 10 000 najważniejszych pojęć dla szybkości SVD
    vocab = sorted(vocab, key=lambda t: df[t], reverse=True)[:10000]
    term_to_idx = {term: i for i, term in enumerate(vocab)}

    rows, cols, vals = [], [], []
    for doc_idx, tokens in enumerate(tokenized_docs):
        tf = Counter(t for t in tokens if t in term_to_idx)
        doc_len = sum(tf.values())
        if doc_len == 0:
            continue
        for term, freq in tf.items():
            t_idx = term_to_idx[term]
            tf_weight = 1.0 + math.log(freq)
            idf_weight = math.log((1.0 + n_docs) / (1.0 + df[term])) + 1.0
            rows.append(doc_idx)
            cols.append(t_idx)
            vals.append(tf_weight * idf_weight)

    tfidf_matrix = csr_matrix((vals, (rows, cols)), shape=(n_docs, len(vocab)), dtype=np.float64)

    k = min(target_dim, min(tfidf_matrix.shape) - 2)
    if k < 2:
        return [[0.0] * target_dim for _ in range(n_docs)]

    u, s, _ = svds(tfidf_matrix, k=k)
    # Sortowanie składowych od największej wartości osobliwej
    idx_order = np.argsort(-s)
    u = u[:, idx_order]
    s = s[idx_order]
    lsa_vectors = u * s

    # Normalizacja L2 każdego wektora do długości jednostkowej (||v|| = 1.0)
    norms = np.linalg.norm(lsa_vectors, axis=1, keepdims=True)
    norms[norms < 1e-9] = 1.0
    normalized = lsa_vectors / norms

    return [[round(float(x), 5) for x in row] for row in normalized]

def profile_all_researchers(input_file=RESEARCHERS_FILE, output_file=PROFILES_FILE):
    path = Path(input_file)
    if not path.exists():
        path = ROOT_DIR / "krok_1_pozyskanie_danych" / "researchers.json"
    if not path.exists():
        path = ROOT_DIR / "researchers.json"

    if not path.exists():
        print(f"[BŁĄD] Nie znaleziono pliku {input_file}. Uruchom najpierw Krok 1!")
        return []

    with open(path, "r", encoding="utf-8") as f:
        researchers = json.load(f)

    print("=" * 72)
    print("WEIMAR RESEARCH HUB — KROK 2: PROFILOWANIE NAUKOWCÓW (WSZYSTKIE DZIEDZINY)")
    print(f"Liczba naukowców do sprofilowania: {len(researchers)}")
    print("=" * 72)

    comp_infos = []
    domain_counts = Counter()

    for r in researchers:
        comp = extract_competencies(r)
        comp_infos.append(comp)
        domain_counts[comp["primary_domain"]] += 1

    # Wyznaczenie wektorów semantycznych dla całego zbioru
    embeddings = build_semantic_embeddings(researchers, comp_infos, target_dim=128)

    profiled = []
    for idx, (r, comp, emb) in enumerate(zip(researchers, comp_infos, embeddings), 1):
        rec = dict(r)
        rec["primary_domain"] = comp["primary_domain"]
        rec["secondary_domain"] = comp["secondary_domain"]
        rec["competencies"] = comp["competencies"]
        rec["profile_summary"] = generate_profile_summary(r, comp)
        rec["embedding"] = emb
        profiled.append(rec)

    print("\nROZKŁAD GŁÓWNYCH OBSZARÓW NAUKOWYCH PO PROFILOWANIU:")
    for dom, cnt in domain_counts.most_common():
        print(f"   - {dom}: {cnt} naukowców")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(profiled, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Zapisano sprofilowane dane do: {output_file}")

    local_out = CURRENT_DIR / "researchers_profiled.json"
    with open(local_out, "w", encoding="utf-8") as f:
        json.dump(profiled, f, ensure_ascii=False, indent=2)

    try:
        from database.db import save_researchers_to_db
        save_researchers_to_db(profiled, reset=True)
    except Exception as e:
        print(f"[DB] Informacja: {e}")

    return profiled

if __name__ == "__main__":
    profile_all_researchers()
