# scripts/inspect_json.py
"""
Affiche la structure d'un fichier JSON : clés, types, profondeur.
Usage : python scripts/inspect_json.py data/raw/api_football/premier_league_2022_fixtures.json
"""
import json
import sys
from pathlib import Path


def inspect(obj, indent=0, max_items=2, max_depth=4):
    """Parcourt récursivement un objet JSON et affiche sa structure."""
    prefix = "  " * indent

    if indent > max_depth:
        print(f"{prefix}... (profondeur max atteinte)")
        return

    if isinstance(obj, dict):
        for key, value in obj.items():
            value_type = type(value).__name__
            if isinstance(value, (dict, list)):
                print(f"{prefix}{key}: {value_type}")
                inspect(value, indent + 1, max_items, max_depth)
            else:
                sample = repr(value)[:60]
                print(f"{prefix}{key}: {value_type} = {sample}")

    elif isinstance(obj, list):
        print(f"{prefix}[liste de {len(obj)} élément(s)]")
        for item in obj[:max_items]:
            inspect(item, indent + 1, max_items, max_depth)
        if len(obj) > max_items:
            print(f"{prefix}... ({len(obj) - max_items} autres éléments non affichés)")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/inspect_json.py <chemin_vers_fichier.json> [max_depth]")
        sys.exit(1)

    filepath = Path(sys.argv[1])
    max_depth = int(sys.argv[2]) if len(sys.argv) > 2 else 4

    if not filepath.exists():
        print(f"Fichier introuvable : {filepath}")
        sys.exit(1)

    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    print(f"=== Structure de {filepath.name} ===\n")
    inspect(data, max_depth=max_depth)

if __name__ == "__main__":
    main()