"""Validate and zip the course materials with the required single root directory."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if ROOT.name == "uruchomienie":
    ROOT = ROOT.parent
CONTENTS = ("README.md", "sprawozdanie.pdf", "prezentacja.pdf", "project_metadata.json",
            "kod", "dane", "modele", "wyniki", "uruchomienie")


def validate():
    from pypdf import PdfReader
    for name in CONTENTS:
        if not (ROOT / name).exists():
            raise ValueError(f"Missing required item: {name}")
    pages = len(PdfReader(ROOT / "sprawozdanie.pdf").pages)
    if not 5 <= pages <= 10:
        raise ValueError(f"Course report must have 5-10 pages; got {pages}")
    slides = len(PdfReader(ROOT / "prezentacja.pdf").pages)
    if not slides:
        raise ValueError("Presentation PDF is empty")
    for name in ("instrukcja_uruchomienia.pdf", "wymagania.txt"):
        if not (ROOT / "uruchomienie" / name).is_file():
            raise ValueError(f"Missing startup file: {name}")
    read_json = lambda p: json.loads((ROOT / p).read_text(encoding="utf-8"))
    config = read_json("kod/godot_game/config/balance.json")
    if config != read_json("dane/config/balance.json") or config != read_json("modele/balance_snapshot.json"):
        raise ValueError("Code, input data and model balance snapshots differ")
    map_data = read_json("kod/godot_game/config/map_data.json")
    if map_data != read_json("dane/config/map_data.json") or map_data != read_json("modele/map_snapshot.json"):
        raise ValueError("Code, input data and model map snapshots differ")
    report = read_json("wyniki/eksperyment/report.json")
    fingerprint = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    if fingerprint != report["config_sha256"]:
        raise ValueError("Results use a different balance")
    if read_json("modele/best_strategy.json") != report["strategy"]:
        raise ValueError("Packaged model differs from the reported winner")
    if not (ROOT / "kod/godot_game/project.godot").is_file():
        raise ValueError("Godot project is missing")
    if not (ROOT / "wyniki/wykresy/rozwoj_jakosci_calej_populacji.png").is_file():
        raise ValueError("Whole-population learning curve is missing")
    print(f"Validated: report {pages} pages, presentation {slides} slides; code/data/model/results agree.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--team", type=int)
    parser.add_argument("--check", action="store_true", help="Validate without creating a ZIP")
    args = parser.parse_args()
    metadata_path = ROOT / "project_metadata.json"
    meta = json.loads(metadata_path.read_text(encoding="utf-8"))
    team = args.team if args.team is not None else meta.get("team_number")
    if team is not None and team < 1:
        parser.error("Team number must be positive")
    if args.team is not None and meta.get("team_number") != team:
        meta["team_number"] = team
        meta["submission_note"] = "Numer zespolu podany podczas pakowania."
        for path in (metadata_path, ROOT / "kod/project_metadata.json"):
            path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        readme = ROOT / "README.md"
        text = re.sub(r"Numer zespołu: \*\*.*?\*\*", f"Numer zespołu: **{team}**", readme.read_text(encoding="utf-8"))
        readme.write_text(text, encoding="utf-8")
        subprocess.run([sys.executable, "-m", "src.course_report", "--input", "../../wyniki/eksperyment/report.json",
            "--output", "../../sprawozdanie.pdf"], cwd=ROOT / "kod/python_ai", check=True)
    validate()
    if args.check:
        return
    if team is None:
        parser.error("Podaj numer zespolu z Teams: --team NUMER. Nie mozna zgadnac wymaganej nazwy archiwum.")
    manifest_path = ROOT / "uruchomienie/manifest.json"
    if manifest_path.exists():
        saved = json.loads(manifest_path.read_text(encoding="utf-8"))
        saved["team_number"] = team
        for name in saved.get("sha256", {}):
            saved["sha256"][name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(saved, indent=2), encoding="utf-8")
    verification_path = ROOT / "uruchomienie/weryfikacja.json"
    if verification_path.exists():
        saved = json.loads(verification_path.read_text(encoding="utf-8"))
        saved["team_number"] = team
        verification_path.write_text(json.dumps(saved, indent=2), encoding="utf-8")
    name = f"projekt_{team}_pon_8"
    target = ROOT / f"{name}.zip"
    paths = []
    for name_part in CONTENTS:
        path = ROOT / name_part
        paths.extend([path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file()))
    excluded = {".git", ".godot", ".venv", "__pycache__", ".pytest_cache"}
    paths = [p for p in paths if not excluded.intersection(p.relative_to(ROOT).parts)
             and not p.name.startswith(("~$", ".env")) and p.suffix not in (".pyc", ".tmp")]
    manifest = {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in paths:
            archive.write(path, f"{name}/{path.relative_to(ROOT).as_posix()}")
        archive.writestr(f"{name}/uruchomienie/sha256_paczki.json", json.dumps(manifest, indent=2))
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP integrity check failed")
        if {n.split("/")[0] for n in archive.namelist()} != {name}:
            raise ValueError("ZIP must contain exactly one root folder matching its filename")
    print(f"ZIP ready: {target} ({len(paths)} files); integrity verified.")


if __name__ == "__main__":
    main()
