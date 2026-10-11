"""Extrait les métadonnées des deux premières pages d'un arrêté préfectoral.

Étapes : téléchargement du PDF, extraction du texte des pages 1 et 2 avec pdfplumber, écriture de output/raw_text.txt, puis de
output/arrete.csv.

Qualité d'extraction des clauses VU :
- pdfplumber (extract_text()) restitue correctement les clauses VU longues, sur plusieurs lignes et avec des incises : chaque clause commence en début de ligne, sans espaces parasites dans les mots des champs extraits.
- Le texte est normalisé (apostrophes typographiques) puis aplati (espaces collapsés) avant d'appliquer les regex de contenu. Les clauses sont comptées au début des lignes (VU, CONSIDERANT, SUR).
- Le pied de page ("2/36") est du bruit sans effet sur les champs extraits.
  Certaines lignes de l'en-tête (adresse, téléphone) sont absentes du texte extrait ; elles ne sont pas utilisées ici.

Choix de documentation :
- exploitant : "S.A.S. VALSPAR", nom figurant dans la clause décrivant la demande. "S.A.S. THE VALSPAR Corporation" apparaît plus loin dans le texte.
- adresse : issue de la clause des arrêtés antérieurs, car la clause de la demande est tronquée ("située à Nantes, ;").
- date_signature : vide, la signature est hors périmètre et n'est jamais déduite des dates des clauses VU.
- Toute valeur introuvable reste vide dans le CSV.
"""
import csv
import re
from pathlib import Path

import pdfplumber
import requests

PDF_URL = "https://www.georisques.gouv.fr/webappReport/ws/installations/document/a34c9176e16c45aab2705704ac415621"
PDF_PATH = Path("data/arrete.pdf")
OUTPUT_DIR = Path("output")
NB_PAGES = 2


def download_pdf() -> Path:
    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(PDF_URL, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    PDF_PATH.write_bytes(r.content)
    return PDF_PATH

def extract_pages(path: Path) -> list[str]:
    with pdfplumber.open(path) as pdf:
        return [(p.extract_text() or "") for p in pdf.pages[:NB_PAGES]]

def normalize(text: str) -> str:
    return text.replace("\u2019", "'").replace("\u2018", "'")

def first(pattern: str, text: str, flags=0, group=1) -> str:
    m = re.search(pattern, text, flags)
    return re.sub(r"\s+", " ", m.group(group)).strip() if m else ""

def build_row(text: str) -> dict:
    flat = re.sub(r"\s+", " ", text)
    m_pref = re.search(r"^PREFECTURE (DE LA|DU|DE) ([A-ZÉ' -]+)$", text, re.M)
    prefecture = ""
    if m_pref:
        prefecture = f"Préfecture {m_pref.group(1).lower()} {m_pref.group(2).title()}"
    m_addr = re.search(r"située à ([^,;]+), (\d+[^;]*?)\s*;", flat)
    adresse = f"{m_addr.group(2).strip()}, {m_addr.group(1).strip()}" if m_addr else ""
    return {
        "reference": first(r"\b(\d{4}\s+[A-Z]{2,8}\s*/\s*\d+)\b", flat),
        "date_signature": "",
        "exploitant": first(r"demande présentée par (?:la |le )?(.+?)(?:,| en vue)", flat),
        "adresse": adresse,
        "prefecture": prefecture,
        "objet": first(r"en vue d'(?:obtenir )?(l'autorisation .+?)(?: située|\s*;)", flat),
        "nb_clauses_vu": len(re.findall(r"^VU\b", text, re.M)),
        "nb_clauses_considerant": len(re.findall(r"^CONSIDERANT\b", text, re.M)),
        "nb_clauses_sur": len(re.findall(r"^SUR\b", text, re.M)),
    }

def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    pages = extract_pages(download_pdf())
    raw = "\n".join(f"=== PAGE {i} ===\n{t}\n" for i, t in enumerate(pages, 1))
    (OUTPUT_DIR / "raw_text.txt").write_text(raw, encoding="utf-8")

    row = build_row(normalize("\n".join(pages)))
    with open(OUTPUT_DIR / "arrete.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row), delimiter=";")
        w.writeheader()
        w.writerow(row)
    print("OK :", row)

if __name__ == "__main__":
    main()