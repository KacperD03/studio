"""
Serwer REST API dla Weimar Research Hub (KROK 6 — Wszystkie Dziedziny)
Projekt: Weimar Research Hub
Udostępnia endpointy dla:
- Wyszukiwania, filtrowania (kraj, uczelnia, dziedzina) i przeglądania profili naukowców
- Rekomendacji współpracowników (podobieństwo tematyczne vs komplementarność kompetencji)
- Uzasadniania rekomendacji (RAG z cytowaniem konkretnych publikacji)
- Generowania propozycji projektowych dla 2-3 naukowców
- Statystyk i serwowania interfejsu React SPA
"""

import os
import sys
from collections import Counter
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from krok_3_rekomendacje.recommend import PartnerRecommender
from krok_4_uzasadnienia.explain import RecommendationExplainer
from krok_5_propozycje.generate_proposals import ProposalGenerator

FRONTEND_DIR = CURRENT_DIR.parent / "frontend"

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")

# Globalne instancje modułów
recommender = None
explainer = None
proposal_gen = None

def ensure_modules():
    global recommender, explainer, proposal_gen
    if recommender is None:
        recommender = PartnerRecommender()
    if explainer is None:
        explainer = RecommendationExplainer()
    if proposal_gen is None:
        proposal_gen = ProposalGenerator()

@app.route("/")
def index():
    return send_from_directory(str(FRONTEND_DIR), "index.html")

@app.route("/api/researchers", methods=["GET"])
def get_researchers():
    """Zwraca listę naukowców z filtrowaniem i sortowaniem."""
    ensure_modules()
    country = request.args.get("country")
    affiliation = request.args.get("affiliation")
    domain = request.args.get("domain")
    field = request.args.get("field")
    sort_by = request.args.get("sort", "cited")  # 'cited', 'h_index', 'name'
    q = request.args.get("q", "").lower().strip()

    filtered = []
    for r in recommender.researchers:
        if country and r.get("country") != country:
            continue
        if affiliation and r.get("affiliation") != affiliation:
            continue
        if domain and r.get("primary_domain") != domain:
            continue
        if field and r.get("field") != field:
            continue
        if q:
            name_match = q in r.get("name", "").lower()
            field_match = q in r.get("field", "").lower()
            topic_match = any(q in t.lower() for t in r.get("topics", []))
            comp_match = any(q in c.lower() for c in r.get("competencies", []))
            if not (name_match or field_match or topic_match or comp_match):
                continue

        filtered.append({
            "openalex_id": r.get("openalex_id"),
            "name": r.get("name"),
            "orcid": r.get("orcid"),
            "country": r.get("country"),
            "affiliation": r.get("affiliation"),
            "affiliation_full": r.get("affiliation_full"),
            "city": r.get("city"),
            "field": r.get("field"),
            "subfield": r.get("subfield"),
            "primary_domain": r.get("primary_domain"),
            "secondary_domain": r.get("secondary_domain"),
            "competencies": r.get("competencies", [])[:5],
            "works_count": r.get("works_count", 0),
            "cited_by_count": r.get("cited_by_count", 0),
            "h_index": r.get("h_index", 0),
            "publications_count": len(r.get("publications", []))
        })

    if sort_by == "h_index":
        filtered.sort(key=lambda x: x["h_index"], reverse=True)
    elif sort_by == "name":
        filtered.sort(key=lambda x: x["name"])
    else:
        filtered.sort(key=lambda x: x["cited_by_count"], reverse=True)

    return jsonify({
        "total": len(filtered),
        "results": filtered
    })

@app.route("/api/researchers/<author_id>", methods=["GET"])
def get_researcher_detail(author_id):
    """Zwraca pełny profil pojedynczego naukowca wraz z publikacjami i abstraktami."""
    ensure_modules()
    r = recommender.by_id.get(author_id)
    if not r:
        return jsonify({"error": "Naukowiec nie został odnaleziony"}), 404

    rec = dict(r)
    rec.pop("embedding", None)
    return jsonify(rec)

@app.route("/api/recommendations", methods=["GET"])
def get_recommendations():
    """Generuje ranking rekomendacji współpracowników."""
    ensure_modules()
    source_id = request.args.get("source_id")
    mode = request.args.get("mode", "similarity")
    top_k = int(request.args.get("top_k", 6))
    different_country = request.args.get("different_country", "false").lower() == "true"
    country_filter = request.args.get("country") or None

    if not source_id or source_id not in recommender.by_id:
        return jsonify({"error": "Błędne ID naukowca źródłowego"}), 400

    if mode == "complementarity":
        recs = recommender.recommend_by_complementarity(
            source_id, top_k=top_k, country_filter=country_filter, different_country_only=different_country
        )
    else:
        recs = recommender.recommend_by_similarity(
            source_id, top_k=top_k, country_filter=country_filter, different_country_only=different_country
        )

    for item in recs:
        item["researcher"].pop("embedding", None)

    return jsonify({
        "source_id": source_id,
        "mode": mode,
        "count": len(recs),
        "results": recs
    })

@app.route("/api/explain", methods=["POST"])
def explain_collaboration():
    """Zwraca uzasadnienie RAG z odwołaniem do konkretnych publikacji."""
    ensure_modules()
    data = request.get_json() or {}
    source_id = data.get("source_id")
    target_id = data.get("target_id")
    rec_type = data.get("mode", "complementarity")

    if not source_id or not target_id:
        return jsonify({"error": "Wymagane source_id oraz target_id"}), 400

    result = explainer.explain_recommendation(source_id, target_id, rec_type=rec_type)
    return jsonify(result)

@app.route("/api/proposals", methods=["POST"])
def generate_proposal():
    """Generuje propozycję projektu badawczego dla 2-3 naukowców."""
    ensure_modules()
    data = request.get_json() or {}
    researcher_ids = data.get("researcher_ids", [])

    if not (2 <= len(researcher_ids) <= 3):
        return jsonify({"error": "Należy podać od 2 do 3 identyfikatorów naukowców"}), 400

    proposal = proposal_gen.generate_proposal(researcher_ids)
    return jsonify(proposal)

@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Zwraca statystyki bazy naukowców oraz listy dziedzin do filtrów."""
    ensure_modules()
    country_counts = Counter(r.get("country") for r in recommender.researchers)
    inst_counts = Counter((r.get("country"), r.get("affiliation")) for r in recommender.researchers)
    domain_counts = Counter(r.get("primary_domain") for r in recommender.researchers)
    field_counts = Counter(r.get("field") for r in recommender.researchers if r.get("field"))
    oa_domain_counts = Counter(r.get("openalex_domain") for r in recommender.researchers if r.get("openalex_domain"))

    total_pubs = sum(len(r.get("publications", [])) for r in recommender.researchers)
    total_abstracts = sum(
        sum(1 for p in r.get("publications", []) if p.get("abstract"))
        for r in recommender.researchers
    )

    return jsonify({
        "total_researchers": len(recommender.researchers),
        "total_publications": total_pubs,
        "total_abstracts": total_abstracts,
        "countries": dict(country_counts),
        "institutions": {f"{c} ({inst})": cnt for (c, inst), cnt in sorted(inst_counts.items())},
        "domains": dict(domain_counts.most_common()),
        "fields": dict(field_counts.most_common()),
        "openalex_domains": dict(oa_domain_counts.most_common())
    })

if __name__ == "__main__":
    ensure_modules()
    port = int(os.environ.get("PORT", 5000))
    print("=" * 72)
    print(f"Serwer Weimar Research Hub działa pod adresem: http://localhost:{port}")
    print("=" * 72)
    app.run(host="0.0.0.0", port=port, debug=False)
