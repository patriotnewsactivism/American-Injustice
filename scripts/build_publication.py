#!/usr/bin/env python3
"""Assemble the publication edition from full-rewrite sources.

The source of truth is full-rewrite/. This script deliberately does not pull from
older manuscript exports or analysis files.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "full-rewrite"
OUT = ROOT / "manuscript-exports" / "prepublication"
OUT.mkdir(parents=True, exist_ok=True)

DATE = "2026-08-22"
STEM = f"American_Injustice_PUBLICATION_{DATE}"


def source_files(include_manual_toc: bool = True) -> list[Path]:
    files = [p for p in SRC.glob("*.md") if p.name != "OUTLINE.md"]
    files.sort(key=lambda p: p.name)
    if not include_manual_toc:
        files = [p for p in files if p.name != "000_contents.md"]
    return files


def headingize(path: Path, text: str) -> str:
    """Turn each source file's plain-text opening label into a real H1."""
    if path.name in {"0000_front_matter.md", "000_contents.md"}:
        return text.rstrip() + "\n"

    lines = text.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("#", "<")):
            break
        if re.match(
            r"^(A NOTE FROM THE AUTHOR|PROLOGUE\b|CHAPTER\s+\d+\b|EPILOGUE\b|LEGAL ANALYSIS$|APPENDIX$)",
            stripped,
            flags=re.I,
        ):
            lines[i] = "# " + stripped
        break
    return "\n".join(lines).rstrip() + "\n"


def assemble(include_manual_toc: bool = True) -> tuple[str, list[Path]]:
    parts: list[str] = []
    files = source_files(include_manual_toc)
    for p in files:
        text = p.read_text(encoding="utf-8")
        parts.append(headingize(p, text))
    return "\n\n".join(parts).rstrip() + "\n", files


def validate(text: str, files: list[Path]) -> list[str]:
    problems: list[str] = []

    chapter_files = [p for p in files if re.match(r"^\d{2}_chapter\d+_", p.name)]
    numbers = []
    for p in chapter_files:
        m = re.match(r"^(\d{2})_chapter(\d+)_", p.name)
        if m:
            numbers.append(int(m.group(2)))
    if numbers != list(range(1, 40)):
        problems.append(f"Chapter file sequence is not 1-39: {numbers}")

    headings = [int(n) for n in re.findall(r"^#\s+CHAPTER\s+(\d+)\b", text, flags=re.M | re.I)]
    if headings != list(range(1, 40)):
        problems.append(f"Chapter heading sequence is not 1-39: {headings}")

    required = [
        "Copyright © 2026 Matthew Oliver Reardon",
        "DEDICATION",
        "A NOTE FROM THE AUTHOR",
        "PROLOGUE",
        "CHAPTER 39",
        "EPILOGUE",
        "LEGAL ANALYSIS",
        "APPENDIX",
        "STANDING CORRECTIONS FROM EARLIER EDITIONS",
    ]
    for needle in required:
        if needle not in text:
            problems.append(f"Required publication element missing: {needle}")

    forbidden = {
        "[TO BE ASSIGNED]": "ISBN placeholder",
        "ISBN: [Pending]": "ISBN placeholder",
        "Minors are not named": "obsolete privacy claim",
        "minors are not named": "obsolete privacy claim",
        "least reliable narrator": "obsolete self-impeaching author-note language",
        "$129.25 fine": "obsolete Crowder amount",
        "three courts vindicated": "obsolete overstatement",
        "fully vacated my 2022 conviction": "obsolete PCR overstatement",
        "full vacatur of my 2022 conviction": "obsolete PCR overstatement",
    }
    for needle, label in forbidden.items():
        if needle in text:
            problems.append(f"Forbidden stale phrase present ({label}): {needle}")

    # Known chronology / holding guardrails.
    guardrails = [
        "The underlying 2022 aggravated-stalking conviction was not vacated",
        "did not reverse the underlying Justice Court convictions",
        "The New Orleans City Hall case does not contain proof that RTCC footage",
        "is not a criminal adjudication of perjury",
        "did not obtain a merits judgment in my favor",
    ]
    for needle in guardrails:
        if needle not in text:
            problems.append(f"Correction guardrail missing: {needle}")

    return problems


def write_css() -> Path:
    css = r"""
@page {
  size: 6in 9in;
  margin-top: 0.72in;
  margin-bottom: 0.70in;
  @bottom-center { content: counter(page); font-family: Georgia, 'Times New Roman', serif; font-size: 8pt; color: #666; }
}
@page:left { margin-left: 0.66in; margin-right: 0.80in; }
@page:right { margin-left: 0.80in; margin-right: 0.66in; }

html { font-size: 100%; }
body {
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 10.4pt;
  line-height: 1.43;
  color: #111;
  hyphens: auto;
  text-rendering: optimizeLegibility;
}
p {
  text-align: justify;
  margin: 0 0 0.64em;
  widows: 3;
  orphans: 3;
}
h1 {
  break-before: page;
  page-break-before: always;
  font-size: 16.5pt;
  line-height: 1.18;
  text-align: center;
  letter-spacing: 0.035em;
  text-transform: uppercase;
  margin: 2.0in 0 1.05in;
  font-weight: 600;
}
h2 {
  font-size: 12.2pt;
  line-height: 1.25;
  margin: 1.15em 0 0.55em;
  break-after: avoid;
  page-break-after: avoid;
}
h3 { font-size: 10.8pt; break-after: avoid; page-break-after: avoid; }
blockquote {
  margin: 0.9em 1.05em;
  padding-left: 0.8em;
  border-left: 1.5pt solid #aaa;
  font-size: 9.7pt;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin: 0.8em 0 1.05em;
  font-size: 8.3pt;
  line-height: 1.28;
  break-inside: auto;
}
thead { display: table-header-group; }
tr { break-inside: avoid; page-break-inside: avoid; }
th, td { padding: 0.32em 0.38em; vertical-align: top; border-bottom: 0.5pt solid #bbb; }
th { text-align: left; font-weight: 700; border-bottom: 1pt solid #555; }
ul, ol { margin-top: 0.35em; margin-bottom: 0.7em; }
li { margin-bottom: 0.2em; }
hr { border: 0; border-top: 0.6pt solid #aaa; margin: 1.2em auto; width: 42%; }

.title-page, .copyright-page, .dedication-page { break-before: auto; }
.title-page h1 {
  break-before: auto;
  page-break-before: auto;
  font-size: 25pt;
  margin: 0 0 0.6em;
  letter-spacing: 0.08em;
}
.copyright-page h2, .dedication-page h2 {
  break-before: auto;
  page-break-before: auto;
  margin-top: 0;
}
.toc { break-before: page; page-break-before: always; }
.toc h1 { break-before: auto; page-break-before: auto; }

em { font-style: italic; }
strong { font-weight: 700; }
a { color: inherit; text-decoration: none; }
""".strip() + "\n"
    path = OUT / "publication.css"
    path.write_text(css, encoding="utf-8")
    return path


def main() -> None:
    text, files = assemble(True)
    problems = validate(text, files)
    if problems:
        raise SystemExit("PUBLICATION QA FAILED:\n- " + "\n- ".join(problems))

    md_path = OUT / f"{STEM}.md"
    md_path.write_text(text, encoding="utf-8")

    epub_text, _ = assemble(False)
    epub_path = OUT / f"{STEM}_EPUB_SOURCE.md"
    epub_path.write_text(epub_text, encoding="utf-8")

    css_path = write_css()

    word_count = len(re.findall(r"\b[\w'’-]+\b", re.sub(r"<[^>]+>", " ", text)))
    source_digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    report = (
        f"American Injustice publication build\n"
        f"Build date: {DATE}\n"
        f"Source directory: full-rewrite/\n"
        f"Source files assembled: {len(files)}\n"
        f"Chapters: 39\n"
        f"Approximate assembled word count: {word_count:,}\n"
        f"Assembled Markdown SHA-256: {source_digest}\n"
        f"QA: PASS\n"
    )
    (OUT / "BUILD_REPORT.txt").write_text(report, encoding="utf-8")
    print(report)
    print(f"Wrote {md_path.relative_to(ROOT)}")
    print(f"Wrote {epub_path.relative_to(ROOT)}")
    print(f"Wrote {css_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
