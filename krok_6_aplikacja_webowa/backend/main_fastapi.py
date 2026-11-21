"""
FastAPI Implementation for Weimar Research Hub (KROK 6)
Zgodnie z wymaganiami technicznymi zadania: FastAPI, PostgreSQL / SQLite.
Zawiera automatyczną dokumentację Swagger UI pod adresem: /docs
"""

import os
import sys
from collections import Counter
from pathlib import Path
from typing import List, Optional

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from fastapi import FastAPI, Query, HTTPException, Body
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except Exception:
    FASTAPI_AVAILABLE = False

from krok_3_rekomendacje.recommend import PartnerRecommender
from krok_4_uzasadnienia.explain import RecommendationExplainer
from krok_5_propozycje.generate_proposals import ProposalGenerator

if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="Weimar Research Hub API",
        description="Inteligentny system rekomendacji partnerów naukowych z Polski, Niemiec i Francji (Wszystkie dziedziny nauki).",
        version="2.0.0"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    recommender = PartnerRecommender()
    explainer = RecommendationExplainer()
    proposal_gen = ProposalGenerator()

    class ExplainRequest(BaseModel):
        source_id: str
        target_id: str
        mode: Optional[str] = "complementarity"

    class ProposalRequest(BaseModel):
        researcher_ids: List[str]

    @app.get("/api/researchers")
    def get_researchers(
        country: Optional[str] = None,
        affiliation: Optional[str] = None,
        domain: Optional[str] = None,
        field: Optional[str] = None,
        sort: str = "cited",
        q: Optional[str] = None
    ):
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
                ql = q.lower().strip()
                name_match = ql in r.get("name", "").lower()
                field_match = ql in r.get("field", "").lower()
                topic_match = any(ql in t.lower() for t in r.get("topics", []))
                comp_match = any(ql in c.lower() for c in r.get("competencies", []))
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

        if sort == "h_index":
            filtered.sort(key=lambda x: x["h_index"], reverse=True)
        elif sort == "name":
            filtered.sort(key=lambda x: x["name"])
        else:
            filtered.sort(key=lambda x: x["cited_by_count"], reverse=True)

        return {"total": len(filtered), "results": filtered}

    @app.get("/api/researchers/{author_id}")
    def get_researcher_detail(author_id: str):
        r = recommender.by_id.get(author_id)
        if not r:
            raise HTTPException(status_code=404, detail="Researcher not found")
        rec = dict(r)
        rec.pop("embedding", None)
        return rec

    @app.get("/api/recommendations")
    def get_recommendations(
        source_id: str,
        mode: str = "similarity",
        top_k: int = 5,
        different_country: bool = False,
        country: Optional[str] = None
    ):
        if source_id not in recommender.by_id:
            raise HTTPException(status_code=400, detail="Invalid source_id")
        
        if mode == "complementarity":
            recs = recommender.recommend_by_complementarity(
                source_id, top_k=top_k, country_filter=country, different_country_only=different_country
            )
        else:
            recs = recommender.recommend_by_similarity(
                source_id, top_k=top_k, country_filter=country, different_country_only=different_country
            )
        
        for item in recs:
            item["researcher"].pop("embedding", None)
            
        return {"source_id": source_id, "mode": mode, "results": recs}

    @app.post("/api/explain")
    def explain_recommendation(payload: ExplainRequest):
        res = explainer.explain_recommendation(payload.source_id, payload.target_id, rec_type=payload.mode)
        return res

    @app.post("/api/proposals")
    def generate_proposal_endpoint(payload: ProposalRequest):
        if not (2 <= len(payload.researcher_ids) <= 3):
            raise HTTPException(status_code=400, detail="Wymagane 2-3 identyfikatory naukowców")
        res = proposal_gen.generate_proposal(payload.researcher_ids)
        return res

    @app.get("/api/stats")
    def get_stats():
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
        return {
            "total_researchers": len(recommender.researchers),
            "total_publications": total_pubs,
            "total_abstracts": total_abstracts,
            "countries": dict(country_counts),
            "institutions": {f"{c} ({inst})": cnt for (c, inst), cnt in sorted(inst_counts.items())},
            "domains": dict(domain_counts.most_common()),
            "fields": dict(field_counts.most_common()),
            "openalex_domains": dict(oa_domain_counts.most_common())
        }

    # Frontend Static Serving
    FRONTEND_DIR = CURRENT_DIR.parent / "frontend"
    if FRONTEND_DIR.exists():
        @app.get("/")
        def serve_index():
            return FileResponse(str(FRONTEND_DIR / "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_fastapi:app", host="0.0.0.0", port=8000, reload=True)

