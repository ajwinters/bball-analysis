"""Create a new area or idea folder from templates/analysis/, then rebuild INDEX.md.

    pixi run new reffing                                   # analyses/reffing/
    pixi run new reffing/late-calls-by-crew-chief \\
        -q "Number of calls in the last 5 minutes of a game, by crew chief" \\
        -t officiating,clutch
    pixi run new reffing/star-call-rate -q "Calls per possession for star players"

An area is any subject you want to explore. Ideas are the specific lines of thought
inside it, one folder each directly under the area (analyses/reffing/star-call-rate/),
one level deep. INDEX.md lists them in the order created.

Support files are prefixed with _ so they sort together above the ideas:
area: README.md _notebook.py _docs/ _figures/ _tables/; idea: README.md notebook.py _docs/ ...
Tags are free-form; tags.txt lists the usual ones (unknown tags get a warning, not an error).
"""

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSES = ROOT / "analyses"
TEMPLATE = ROOT / "templates" / "analysis"
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def known_tags() -> set[str]:
    lines = (ROOT / "tags.txt").read_text().splitlines()
    return {ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")}


def check_slug(s: str) -> None:
    if not SLUG.match(s):
        sys.exit(f"'{s}': use lowercase letters, digits and single hyphens (e.g. star-call-rate)")


def render(folder: Path, title: str, question: str, tags: list[str], notebook: str) -> None:
    folder.mkdir(parents=True)
    values = {
        "{title}": title,
        "{date}": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        # JSON strings/lists are valid YAML, so quotes and colons in a question are safe
        "{question_yaml}": json.dumps(question),
        "{question}": question,
        "{tags}": json.dumps(tags),
    }
    for src, dst in (("README.md", "README.md"), ("notebook.py", notebook)):
        text = (TEMPLATE / src).read_text()
        for k, v in values.items():
            text = text.replace(k, v)
        (folder / dst).write_text(text)
    for sub in ("_figures", "_tables", "_docs"):
        (folder / sub).mkdir()
        (folder / sub / ".gitkeep").touch()
    print(f"created {folder.relative_to(ROOT)}/")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("path", help="<area> for a new area, or <area>/<idea> for a new idea")
    ap.add_argument("-q", "--question", default="", help="the exact question, in a sentence")
    ap.add_argument("-t", "--tags", default="", help="comma-separated tags, e.g. officiating,clutch")
    a = ap.parse_args()

    tags = [t.strip() for t in a.tags.split(",") if t.strip()]
    unknown = [t for t in tags if t not in known_tags()]
    if unknown:
        print(f"note: new tag(s) {', '.join(unknown)}; add to tags.txt if they'll be reused")

    parts = a.path.strip("/").split("/")
    if len(parts) == 1:
        area = parts[0]
        check_slug(area)
        folder, notebook = ANALYSES / area, "_notebook.py"
        title = area.replace("-", " ").capitalize()
    elif len(parts) == 2:
        area, idea = parts
        if not (ANALYSES / area).is_dir():
            sys.exit(f"no area analyses/{area}/ yet; create it first: pixi run new {area}")
        check_slug(idea)
        folder, notebook = ANALYSES / area / idea, "notebook.py"
        title = idea.replace("-", " ").capitalize()
    else:
        sys.exit("ideas go one level deep: <area>/<idea>")

    if folder.exists():
        sys.exit(f"{folder.relative_to(ROOT)} already exists")
    render(folder, title, a.question, tags, notebook)
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_index.py")], check=True)


if __name__ == "__main__":
    main()
