"""
Skrypt importujący zebrane dane do bazy danych (PostgreSQL / SQLite)
Projekt: Weimar Research Hub
"""

import json
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import RESEARCHERS_FILE
from database.db import init_db, save_researchers_to_db

def run_import():
    print("Inicjalizacja schematu bazy danych...")
    init_db()

    data_file = RESEARCHERS_FILE
    if not data_file.exists():
        data_file = ROOT_DIR / "krok_1_pozyskanie_danych" / "researchers.json"
    if not data_file.exists():
        data_file = ROOT_DIR / "researchers.json"

    if not data_file.exists():
        print(f"[BŁĄD] Brak pliku {RESEARCHERS_FILE}. Pobierz najpierw dane w Kroku 1!")
        return

    with open(data_file, "r", encoding="utf-8") as f:
        researchers = json.load(f)

    print(f"Importowanie {len(researchers)} naukowców do bazy...")
    save_researchers_to_db(researchers)
    print("Import zakończony sukcesem!")

if __name__ == "__main__":
    run_import()

