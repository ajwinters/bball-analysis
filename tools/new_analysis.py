"""Create a new analysis or idea folder from templates/analysis/.

    pixi run new shooting corner-threes                     # analyses/shooting-corner-threes/
    pixi run new shooting-corner-threes --idea wing-vs-corner   # .../ideas/wing-vs-corner/
    pixi run new shooting-corner-threes --idea shot-clock --parent wing-vs-corner

Then rebuilds INDEX.md.
"""

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSES = ROOT / "analyses"
TEMPLATE = ROOT / "templates" / "analysis"
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def topics() -> list[str]:
    lines = (ROOT / "topics.txt").read_text().splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]


def check_slug(s: str) -> None:
    if not SLUG.match(s):
        sys.exit(f"'{s}': use lowercase letters, digits and single hyphens (e.g. corner-threes)")


def render(folder: Path, title: str, parent: str) -> None:
    folder.mkdir(parents=True)
    for name in ("README.md", "notebook.py"):
        text = (TEMPLATE / name).read_text()
        text = text.replace("{title}", title).replace("{parent}", parent)
        text = text.replace("{date}", dt.date.today().isoformat())
        (folder / name).write_text(text)
    for sub in ("figures", "tables", "docs"):
        (folder / sub).mkdir()
        (folder / sub / ".gitkeep").touch()
    print(f"created {folder.relative_to(ROOT)}/")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("first", help="topic (new analysis) or existing analysis folder (with --idea)")
    ap.add_argument("slug", nargs="?", help="slug for a new analysis")
    ap.add_argument("--idea", help="slug of a new idea inside the analysis")
    ap.add_argument("--parent", default="", help="idea this one branches off (same analysis)")
    a = ap.parse_args()

    if a.idea:
        analysis = ANALYSES / a.first
        if not analysis.is_dir():
            sys.exit(f"no analysis folder {analysis.relative_to(ROOT)}")
        check_slug(a.idea)
        if a.parent and not (analysis / "ideas" / a.parent).is_dir():
            sys.exit(f"no idea '{a.parent}' in {a.first}")
        folder = analysis / "ideas" / a.idea
        parent = a.parent or a.first
        title = a.idea.replace("-", " ").capitalize()
    else:
        if not a.slug:
            sys.exit("usage: pixi run new <topic> <slug>   (see --help)")
        if a.first not in topics():
            sys.exit(f"unknown topic '{a.first}'. Known: {', '.join(topics())}. "
                     "Add it to topics.txt if it's really new.")
        check_slug(a.slug)
        folder = ANALYSES / f"{a.first}-{a.slug}"
        parent = a.parent
        title = a.slug.replace("-", " ").capitalize()

    if folder.exists():
        sys.exit(f"{folder.relative_to(ROOT)} already exists")
    render(folder, title, parent)
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_index.py")], check=True)


if __name__ == "__main__":
    main()
