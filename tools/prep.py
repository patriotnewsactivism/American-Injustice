# -*- coding: utf-8 -*-
"""Shared preprocessing: strip the embedded HTML front matter, recover the Part structure."""
import io, re

SRC = "/home/user/American-Injustice/manuscript-exports/American_Injustice_FULL.md"

def load():
    raw = io.open(SRC, encoding="utf-8").read()

    # recover part -> first chapter number, from the embedded HTML toc (line-based)
    lines = raw.split("\n")
    a = next(i for i, l in enumerate(lines) if l.strip() == '<div class="toc">')
    b = next(i for i, l in enumerate(lines) if i > a and l.strip() == "</div>")
    part_at, cur = {}, None
    for l in lines[a:b]:
        m = re.search(r'class="part">([^<]+)<', l)
        if m:
            cur = m.group(1).strip()
            continue
        m = re.search(r'class="n">(\d+)<', l)
        if m and cur:
            part_at[int(m.group(1))] = cur
            cur = None

    # strip <style>...</style> and <div class="toc">...</div>
    clean = re.sub(r"<style>.*?</style>", "", raw, flags=re.S)
    clean = re.sub(r'<div class="toc">.*?\n</div>', "", clean, flags=re.S)
    # drop the draft title block: byline + "Assembled draft ..." stamp (title page supplies these)
    clean = re.sub(r"^\*\*Matthew Oliver Reardon\*\*.*$", "", clean, flags=re.M)
    clean = re.sub(r"^\*Assembled draft.*$", "", clean, flags=re.M)
    # drop leftover rules between the title line and the first real section
    head, sep, rest = clean.partition("# A NOTE FROM THE AUTHOR")
    head = re.sub(r"^-{3,}\s*$", "", head, flags=re.M)
    clean = head + sep + rest
    clean = re.sub(r"\n{3,}", "\n\n", clean)

    assert "<style>" not in clean and 'class="toc"' not in clean and "column-count" not in clean
    return clean, part_at

if __name__ == "__main__":
    c, p = load()
    print("cleaned words:", len(c.split()))
    print("parts:", sorted(p.items()))
