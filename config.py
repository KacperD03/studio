from pathlib import Path

# Bazowe ścieżki projektu
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

RESEARCHERS_FILE = DATA_DIR / "researchers.json"
PROFILES_FILE = DATA_DIR / "researchers_profiled.json"
SQLITE_DB_FILE = DATA_DIR / "weimar.db"

# Uczelnie z Trójkąta Weimarskiego (po 3 z każdego kraju = 9 uczelni)
INSTITUTIONS = [
    # POLSKA (PL)
    {
        "country": "PL",
        "name": "AGH University of Krakow",
        "short_name": "AGH",
        "id": "I686019",
        "city": "Kraków"
    },
    {
        "country": "PL",
        "name": "University of Warsaw",
        "short_name": "UW",
        "id": "I4654613",
        "city": "Warszawa"
    },
    {
        "country": "PL",
        "name": "Warsaw University of Technology",
        "short_name": "PW",
        "id": "I108403487",
        "city": "Warszawa"
    },

    # NIEMCY (DE)
    {
        "country": "DE",
        "name": "Technical University of Munich",
        "short_name": "TUM",
        "id": "I62916508",
        "city": "Monachium"
    },
    {
        "country": "DE",
        "name": "Heidelberg University",
        "short_name": "Heidelberg",
        "id": "I223822909",
        "city": "Heidelberg"
    },
    {
        "country": "DE",
        "name": "Humboldt University of Berlin",
        "short_name": "Humboldt",
        "id": "I39343248",
        "city": "Berlin"
    },

    # FRANCJA (FR)
    {
        "country": "FR",
        "name": "Sorbonne University",
        "short_name": "Sorbonne",
        "id": "I39804081",
        "city": "Paryż"
    },
    {
        "country": "FR",
        "name": "Paris-Saclay University",
        "short_name": "Paris-Saclay",
        "id": "I277688954",
        "city": "Paryż/Saclay"
    },
    {
        "country": "FR",
        "name": "École Normale Supérieure (ENS)",
        "short_name": "ENS",
        "id": "I11559806",
        "city": "Paryż"
    }
]

# Reprezentatywne dziedziny naukowe w OpenAlex (wszystkie główne obszary wiedzy)
DISCIPLINE_FIELDS = [
    {"id": "fields/17", "name": "Computer Science"},
    {"id": "fields/22", "name": "Engineering"},
    {"id": "fields/27", "name": "Medicine"},
    {"id": "fields/13", "name": "Biochemistry, Genetics and Molecular Biology"},
    {"id": "fields/31", "name": "Physics and Astronomy"},
    {"id": "fields/16", "name": "Chemistry"},
    {"id": "fields/25", "name": "Materials Science"},
    {"id": "fields/26", "name": "Mathematics"},
    {"id": "fields/23", "name": "Environmental Science"},
    {"id": "fields/33", "name": "Social Sciences"},
    {"id": "fields/20", "name": "Economics, Econometrics and Finance"},
    {"id": "fields/28", "name": "Neuroscience"},
]

# Liczba pobieranych autorów na dziedzinę i uczelnię (9 * ~90-100 unikalnych = ~800+ naukowców)
AUTHORS_PER_FIELD = 10

# Nagłówki zapytań HTTP do OpenAlex (Polite Pool)
HTTP_HEADERS = {
    "User-Agent": "mailto:weimar.research.hub@student.agh.edu.pl (Weimar Research Hub Project)"
}
