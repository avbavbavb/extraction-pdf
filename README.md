# Extraction d'un arrêté préfectoral

## Prérequis

- uv
- Accès internet

## Exécution

```bash
uv run extract.py
```

Le script télécharge le PDF puis génère :

- `output/raw_text.txt`
- `output/arrete.csv`

## Choix d'extraction

- **Périmètre** : seules les pages 1 et 2 sont lues.
- **Bibliothèque** : `pdfplumber`. Les clauses « VU » longues, sur plusieurs
  lignes, sont bien restituées ligne à ligne ; chaque clause commence en début
  de ligne, ce qui permet de les compter de façon fiable.
- **Normalisation** : les apostrophes typographiques sont remplacées par des
  apostrophes droites et les espaces sont aplatis avant les expressions
  régulières.
- **Exploitant** : `S.A.S. VALSPAR`, nom de la clause décrivant la demande.
  `S.A.S. THE VALSPAR Corporation` est cité plus loin dans le document.
- **Adresse** : lue dans la clause des arrêtés antérieurs, car la clause de la
  demande est tronquée (« située à Nantes, ; »).
- **Date de signature** : vide. La signature se trouve hors périmètre et la date
  n'est jamais déduite des clauses « VU ».
- **Valeurs absentes** : laissées vides dans le CSV, sans erreur.