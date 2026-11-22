"""
ETAP 1: Prosty interfejs webowy (Prototyp MVP na pokaz)
Projekt: Weimar Research Hub

Co robi ten plik:
Uruchamia lekki serwer webowy (Flask lub wbudowany serwer HTTP Pythona,
więc zadziała nawet na komputerze uczelnianym bez zainstalowanego Flaska!), który pozwala:
1. Przeglądać i filtrować bazę 824 naukowców z 9 uczelni (Polska, Niemcy, Francja).
2. Oglądać wygenerowany profil naukowca (kompetencje, biogram, publikacje i abstrakty z OpenAlex).
3. Testować oba algorytmy rekomendacji partnerów:
   - Podobieństwo tematyczne (Cosine Similarity + Jaccard)
   - Komplementarność kompetencji (współpraca interdyscyplinarna)

Uruchomienie (z wewnątrz folderu etap1_prototyp):
    python app.py
Następnie otwórz w przeglądarce: http://localhost:5050
"""

import json
import os
from collections import Counter
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from krok2_profilowanie_i_rekomendacje import SilnikRekomendacji

CURRENT_DIR = Path(__file__).resolve().parent
TEMPLATE_FILE = CURRENT_DIR / "templates" / "index.html"

# Inicjalizacja silnika rekomendacji z lokalnego pliku dane_naukowcy.json
silnik = SilnikRekomendacji()


def build_stats():
    """Zwraca podstawowe statystyki bazy oraz listy uczelni i dziedzin do filtrów."""
    kraje = Counter(r.get("country") for r in silnik.researchers)
    uczelnie = sorted({r.get("affiliation") for r in silnik.researchers if r.get("affiliation")})
    dziedziny = sorted({r.get("primary_domain") for r in silnik.researchers if r.get("primary_domain")})
    liczba_publikacji = sum(len(r.get("publications", [])) for r in silnik.researchers)
    return {
        "total_researchers": len(silnik.researchers),
        "total_publications": liczba_publikacji,
        "countries": dict(kraje),
        "affiliations": uczelnie,
        "domains": dziedziny,
    }


def filter_researchers(country="", affiliation="", domain="", q=""):
    """Zwraca przefiltrowaną listę naukowców."""
    q = q.lower().strip()
    wyniki = []
    for r in silnik.researchers:
        if country and r.get("country") != country:
            continue
        if affiliation and r.get("affiliation") != affiliation:
            continue
        if domain and r.get("primary_domain") != domain:
            continue
        if q:
            tekst = " ".join([
                r.get("name", ""),
                r.get("field", ""),
                r.get("primary_domain", ""),
                " ".join(r.get("competencies", [])),
                " ".join(r.get("topics", [])),
            ]).lower()
            if q not in tekst:
                continue

        wyniki.append({
            "openalex_id": r.get("openalex_id"),
            "name": r.get("name"),
            "country": r.get("country"),
            "affiliation": r.get("affiliation"),
            "affiliation_full": r.get("affiliation_full"),
            "field": r.get("field"),
            "primary_domain": r.get("primary_domain"),
            "h_index": r.get("h_index", 0),
            "cited_by_count": r.get("cited_by_count", 0),
            "works_count": r.get("works_count", 0),
            "competencies": r.get("competencies", [])[:4],
        })

    wyniki.sort(key=lambda x: x["cited_by_count"], reverse=True)
    return {"total": len(wyniki), "results": wyniki[:100]}


def compute_recommendations(source_id, mode="similarity", foreign_only=True, country=None):
    """Zwraca Top-5 rekomendowanych partnerów w wybranym trybie."""
    if source_id not in silnik.by_id:
        return None
    if mode == "complementarity":
        recs = silnik.rekomenduj_komplementarnych(
            source_id, top_k=5, tylko_zagraniczni=foreign_only, kraj=country
        )
    else:
        recs = silnik.rekomenduj_podobnych(
            source_id, top_k=5, tylko_zagraniczni=foreign_only, kraj=country
        )
    return {"source_id": source_id, "mode": mode, "results": recs}


# Próba użycia Flaska (jeśli zainstalowany), w przeciwnym razie wbudowany HTTPServer
try:
    from flask import Flask, jsonify, render_template, request
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

if HAS_FLASK:
    app = Flask(__name__, template_folder=str(CURRENT_DIR / "templates"))

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/stats")
    def api_stats():
        return jsonify(build_stats())

    @app.route("/api/researchers")
    def api_researchers():
        return jsonify(filter_researchers(
            country=request.args.get("country", "").strip(),
            affiliation=request.args.get("affiliation", "").strip(),
            domain=request.args.get("domain", "").strip(),
            q=request.args.get("q", ""),
        ))

    @app.route("/api/researchers/<author_id>")
    def api_researcher_detail(author_id):
        r = silnik.by_id.get(author_id)
        if not r:
            return jsonify({"error": "Nie znaleziono naukowca"}), 404
        return jsonify(silnik._bez_wektora(r))

    @app.route("/api/recommendations")
    def api_recommendations():
        source_id = request.args.get("source_id", "").strip()
        mode = request.args.get("mode", "similarity")
        foreign_only = request.args.get("foreign_only", "true").lower() == "true"
        country = request.args.get("country", "").strip() or None
        res = compute_recommendations(source_id, mode, foreign_only, country)
        if res is None:
            return jsonify({"error": "Nieprawidłowe ID naukowca"}), 400
        return jsonify(res)


class FallbackHandler(BaseHTTPRequestHandler):
    """Wbudowany serwer HTTP — działa bez żadnych zewnętrznych bibliotek (0 pip install)."""

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = {k: v[0] for k, v in parse_qs(parsed.query).items()}

        if path == "/":
            html = TEMPLATE_FILE.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
        elif path == "/api/stats":
            self._send_json(build_stats())
        elif path == "/api/researchers":
            self._send_json(filter_researchers(
                country=qs.get("country", ""),
                affiliation=qs.get("affiliation", ""),
                domain=qs.get("domain", ""),
                q=qs.get("q", ""),
            ))
        elif path.startswith("/api/researchers/"):
            author_id = path.split("/")[-1]
            r = silnik.by_id.get(author_id)
            if not r:
                self._send_json({"error": "Nie znaleziono naukowca"}, 404)
            else:
                self._send_json(silnik._bez_wektora(r))
        elif path == "/api/recommendations":
            res = compute_recommendations(
                source_id=qs.get("source_id", ""),
                mode=qs.get("mode", "similarity"),
                foreign_only=qs.get("foreign_only", "true").lower() == "true",
                country=qs.get("country") or None,
            )
            if res is None:
                self._send_json({"error": "Nieprawidłowe ID naukowca"}, 400)
            else:
                self._send_json(res)
        else:
            self._send_json({"error": "Not found"}, 404)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print("=" * 72)
    print("WEIMAR RESEARCH HUB — PROTOTYP INTERFEJSU (ETAP 1)")
    print(f"Otwórz w przeglądarce: http://localhost:{port}")
    print("=" * 72)
    if HAS_FLASK:
        app.run(host="0.0.0.0", port=port, debug=False)
    else:
        server = HTTPServer(("0.0.0.0", port), FallbackHandler)
        server.serve_forever()
